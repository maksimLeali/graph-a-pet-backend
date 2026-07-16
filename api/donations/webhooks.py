"""Flask endpoint for donation-related Stripe webhooks — plain HTTP by
necessity (Stripe delivers webhooks over HTTP, not GraphQL), everything
else in this feature goes through the GraphQL API per the task.

Verifies the signature, rejects livemode=true while in test mode, persists
the event BEFORE processing (duplicate delivery becomes a no-op via the DB
unique constraint — see repository/donations/webhook_events.py), then
dispatches to domain/donations/webhooks.py. Processing errors are caught
here so a bug never causes an infinite Stripe retry loop on an event we've
already durably logged as FAILED (visible + retryable via
retryStripeWebhookEvent).
"""
import json

import stripe
from flask import Blueprint, request, jsonify

from stripe_connect import get_webhook_secret, get_environment
import repository.donations.webhook_events as webhook_events_data
import domain.donations.webhooks as webhooks_domain
from utils.logger import logger

donations_webhooks = Blueprint("donations_webhooks", __name__, url_prefix="/donations")


@donations_webhooks.route("/webhooks", methods=["POST"])
def stripe_donation_webhook():
	logger.critical('got an event')
	sig_header = request.headers.get("Stripe-Signature", "")

	try:
		secret = get_webhook_secret()
		event = stripe.Webhook.construct_event(request.get_data(), sig_header, secret)
	except Exception:
		logger.exception("donation webhook signature verification failed")
		return jsonify({"error": "invalid signature"}), 400

	logger.critical(f"donation webhook received: id={event['id']} type={event['type']} livemode={event['livemode']}")

	account = getattr(event, "account", None)
	logger.info(
		f"donation webhook received: id={event['id']} type={event['type']} "
		f"livemode={event['livemode']} account={account}"
	)

	if event["livemode"] and get_environment() == "test":
		logger.warning(f"rejecting livemode=true event {event['id']} while running in test mode")
		return jsonify({"error": "livemode event rejected in test mode"}), 400

	# stripe>=8 dropped to_dict(for_json=...); str(StripeObject) emits JSON, so
	# json.loads(str(...)) yields a fully-nested, JSON-safe plain dict.
	stored_event, created = webhook_events_data.create_received_event(
		event["id"], event["type"], event["livemode"], payload=json.loads(str(event)),
	)
	if not created:
		logger.info(f"duplicate webhook delivery for {event['id']}, skipping processing")
		return jsonify({"received": True}), 200

	try:
		# domain/donations/webhooks.py handlers use plain dict .get(...) on
		# every field — event["data"]["object"] is a typed Stripe resource
		# (StripeObject), which has no .get() method (only __getitem__), so
		# it must be converted to a real dict first (same JSON round-trip used
		# a few lines up to make the stored payload JSON-safe)
		webhooks_domain.process_event(
			event["type"], json.loads(str(event["data"]["object"])), account,
		)
		webhook_events_data.mark_processed(stored_event.id)
		logger.info(f"donation webhook processed ok: id={event['id']} type={event['type']}")
	except Exception as e:
		logger.error(f"donation webhook processing failed: id={event['id']} type={event['type']} error={e}")
		logger.exception(f"error processing donation webhook {event['id']} ({event['type']})")
		webhook_events_data.mark_failed(stored_event.id, str(e))

	return jsonify({"received": True}), 200
