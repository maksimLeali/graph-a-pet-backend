"""Two separate webhook endpoints, because they use two different Stripe
webhook mechanisms:

1. `/stripe-connect/webhooks/thin` — "thin" events (small, unversioned
   payload with just a reference to what changed) for V2 connected-account
   requirement/capability changes. Verified with
   `stripe_client.parse_event_notification(...)` — the SDK-typed
   replacement for `constructEvent` when handling v2 events.

2. `/stripe-connect/webhooks/subscriptions` — regular signed events
   (`customer.subscription.*`, `payment_method.*`, ...) for the
   subscription-to-connected-account demo. Verified with the classic
   `stripe.Webhook.construct_event(...)`.

Setting up the endpoints in the Stripe Dashboard (test mode):

  Thin-events endpoint (Developers -> Webhooks -> + Add destination):
    1. Events from: "Connected accounts"
    2. Show advanced options -> Payload style: "Thin"
    3. Events: search "v2" and select
       - v2.core.account[requirements].updated
       - v2.core.account[configuration.merchant].capability_status_updated
       - v2.core.account[configuration.customer].capability_status_updated
    4. Endpoint URL: https://<your-domain>/stripe-connect/webhooks/thin
    5. Copy the signing secret into config.yml stripe.thin_webhook_secret

  Regular subscription-events endpoint:
    1. Events from: "Your account"
    2. Payload style stays the default ("Snapshot" / regular, NOT thin)
    3. Events: customer.subscription.updated, customer.subscription.deleted,
       payment_method.attached, payment_method.detached, customer.updated,
       customer.tax_id.created, customer.tax_id.updated,
       customer.tax_id.deleted, billing_portal.configuration.created,
       billing_portal.configuration.updated, billing_portal.session.created
    4. Endpoint URL: https://<your-domain>/stripe-connect/webhooks/subscriptions
    5. Copy the signing secret into config.yml stripe.webhook_secret

  Local testing with the Stripe CLI (see https://docs.stripe.com/cli/listen):

    stripe listen \\
      --thin-events 'v2.core.account[requirements].updated,v2.core.account[configuration.merchant].capability_status_updated,v2.core.account[configuration.customer].capability_status_updated' \\
      --forward-thin-to localhost:5001/stripe-connect/webhooks/thin

    stripe listen \\
      --events customer.subscription.updated,customer.subscription.deleted,payment_method.attached,payment_method.detached,customer.updated \\
      --forward-to localhost:5001/stripe-connect/webhooks/subscriptions

  `stripe listen` prints a webhook signing secret for each — put the first
  in stripe.thin_webhook_secret and the second in stripe.webhook_secret.
"""
import stripe
from flask import Blueprint, request, jsonify

from stripe_connect import get_stripe_client, get_thin_webhook_secret, get_webhook_secret
from stripe_connect import data as stripe_data
from utils.logger import logger

stripe_webhooks = Blueprint("stripe_webhooks", __name__, url_prefix="/stripe-connect/webhooks")


# ---------------------------------------------------------------------------
# 1. Thin events — connected account requirement/capability changes
# ---------------------------------------------------------------------------

@stripe_webhooks.route("/thin", methods=["POST"])
def thin_events_webhook():
	sig_header = request.headers.get("Stripe-Signature", "")

	try:
		# get_stripe_client()/get_thin_webhook_secret() both raise
		# StripeConfigError while config.yml still has placeholder values —
		# keep them inside the try so a missing/placeholder secret comes
		# back as a normal 400, not an unhandled 500.
		client = get_stripe_client()
		secret = get_thin_webhook_secret()
		notification = client.parse_event_notification(
			request.get_data(), sig_header, secret
		)
	except Exception as e:
		# Signature mismatch, missing secret, or malformed payload — never
		# process an unverified payload.
		logger.error(f"stripe thin webhook signature verification failed: {e}")
		return jsonify({"error": "invalid signature"}), 400

	logger.api(f"stripe thin event received: type={notification.type} id={notification.id}")

	try:
		_handle_thin_event(notification)
	except Exception as e:
		# Per Stripe's webhook contract: log and still 200 on handler bugs
		# so Stripe doesn't retry a payload we've already durably logged;
		# only signature failures above should produce a non-2xx.
		logger.error(f"error handling stripe thin event {notification.id}: {e}")

	return jsonify({"received": True}), 200


def _handle_thin_event(notification):
	"""Dispatch on `notification.type` — these are exactly the
	LOOKUP_TYPE strings from the Dashboard event-type picker.

	`notification.fetch_related_object()` is the SDK-idiomatic way to fetch
	the up-to-date object a thin event refers to (it does the same "GET the
	related resource" step as the JS example's
	`client.v2.core.events.retrieve(thinEvent.id)`, but goes straight to the
	changed object instead of the wrapping Event).
	"""
	if notification.type in (
		"v2.core.account[requirements].updated",
		"v2.core.account[configuration.merchant].capability_status_updated",
		"v2.core.account[configuration.customer].capability_status_updated",
	):
		account = notification.fetch_related_object()
		logger.api(
			f"connected account {account.id} requirements/capabilities changed "
			f"(event={notification.type})"
		)
		# TODO: this sample never stores onboarding/capability status in the
		# DB (the task asks us to always read it live from the API — see
		# stripe_connect/service.get_account_status). If your integration
		# does cache it for e.g. a dashboard badge, this is where you'd
		# write the refreshed `account.requirements` / capability status.
		return

	logger.api(f"unhandled thin event type: {notification.type}")


# ---------------------------------------------------------------------------
# 2. Regular signed events — subscription lifecycle
# ---------------------------------------------------------------------------

@stripe_webhooks.route("/subscriptions", methods=["POST"])
def subscription_events_webhook():
	sig_header = request.headers.get("Stripe-Signature", "")

	try:
		secret = get_webhook_secret()
		event = stripe.Webhook.construct_event(
			request.get_data(), sig_header, secret
		)
	except Exception as e:
		logger.error(f"stripe subscription webhook signature verification failed: {e}")
		return jsonify({"error": "invalid signature"}), 400

	logger.api(f"stripe event received: type={event['type']} id={event['id']}")

	try:
		_handle_subscription_event(event)
	except Exception as e:
		logger.error(f"error handling stripe event {event['id']}: {e}")

	return jsonify({"received": True}), 200


def _handle_subscription_event(event):
	event_type = event["type"]
	obj = event["data"]["object"]

	if event_type == "customer.subscription.updated":
		_handle_subscription_updated(obj)
	elif event_type == "customer.subscription.deleted":
		_handle_subscription_deleted(obj)
	elif event_type == "payment_method.attached":
		# TODO: write to DB — a real integration would record which payment
		# method the connected account attached, e.g.:
		#   db_upsert_payment_method(account_id=obj["customer_account"], payment_method_id=obj["id"])
		logger.api(f"payment method attached: {obj.get('id')}")
	elif event_type == "payment_method.detached":
		# TODO: write to DB — remove/mark-detached the payment method row.
		logger.api(f"payment method detached: {obj.get('id')}")
	elif event_type == "customer.updated":
		# TODO: write to DB — sync `invoice_settings.default_payment_method`
		# if you store a default payment method per account. Billing info
		# only — never use the billing email as a login credential.
		logger.api(f"customer/account billing info updated: {obj.get('id')}")
	elif event_type in (
		"customer.tax_id.created",
		"customer.tax_id.updated",
		"customer.tax_id.deleted",
	):
		# TODO: write to DB — store tax ID + validation status if your
		# integration collects them. See https://docs.stripe.com/billing/customer/tax-ids
		logger.api(f"tax id event: {event_type} for {obj.get('id')}")
	elif event_type in (
		"billing_portal.configuration.created",
		"billing_portal.configuration.updated",
		"billing_portal.session.created",
	):
		# Informational only in this sample — nothing to persist.
		logger.api(f"billing portal event: {event_type}")
	else:
		logger.api(f"unhandled stripe event type: {event_type}")


def _handle_subscription_updated(subscription):
	# IMPORTANT (per the task's "General Tips"): V2 connected accounts do
	# NOT have a `.customer` — use `.customer_account` (an acct_... id) to
	# find which connected account this subscription belongs to.
	account_id = subscription.get("customer_account")
	if not account_id:
		logger.error(
			f"subscription {subscription.get('id')} has no customer_account — "
			"skipping (is this a V1/non-Connect subscription?)"
		)
		return

	items = subscription.get("items", {}).get("data", [])
	price_id = items[0]["price"]["id"] if items else None
	pause_collection = subscription.get("pause_collection")

	logger.api(
		f"subscription {subscription['id']} for account {account_id}: "
		f"status={subscription['status']} price={price_id} "
		f"cancel_at_period_end={subscription.get('cancel_at_period_end')} "
		f"paused={bool(pause_collection)}"
	)

	# Store/refresh status in the DB (see stripe_connect/data.py) — this is
	# the one webhook flow in this sample that DOES write to the DB, since
	# subscription status (unlike Connect onboarding status) is exactly the
	# kind of thing you should cache rather than call Stripe for on every
	# page load.
	stripe_data.upsert_subscription(
		stripe_subscription_id=subscription["id"],
		stripe_account_id=account_id,
		price_id=price_id,
		status=subscription["status"],
		cancel_at_period_end=bool(subscription.get("cancel_at_period_end")),
	)


def _handle_subscription_deleted(subscription):
	account_id = subscription.get("customer_account")
	logger.api(f"subscription {subscription['id']} for account {account_id} canceled/deleted")
	# Revoke access here if this sample gated any feature on subscription
	# status. Keeping the row (marked canceled) rather than deleting it, so
	# there's an audit trail of what the account was subscribed to.
	stripe_data.upsert_subscription(
		stripe_subscription_id=subscription["id"],
		stripe_account_id=account_id,
		price_id=(subscription.get("items", {}).get("data") or [{}])[0].get("price", {}).get("id"),
		status="canceled",
		cancel_at_period_end=bool(subscription.get("cancel_at_period_end")),
	)
