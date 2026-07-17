"""Donation-related Stripe webhook event processing.

Handles the classic (non-thin), signed v1 events listed in the task:
payment_intent.{processing,succeeded,payment_failed,canceled},
charge.refunded, charge.dispute.{created,updated,closed}, account.updated,
payout.{created,paid,failed} — plus one addition beyond the task's minimum
list, `setup_intent.succeeded`, needed to close the saved-payment-method
loop (there is no `confirmPaymentMethodSetup` mutation in the task's spec,
so the webhook is the only place a SetupIntent's resulting PaymentMethod
can be persisted). This is a DIFFERENT webhook mechanism than the
stripe_connect/ sample's thin-events endpoint (V2 account
requirement/capability changes) — these are classic Connect webhooks,
verified with `stripe.Webhook.construct_event` against `webhook_secret`.

Every event is persisted (StripeWebhookEvent) BEFORE processing, and
duplicate/out-of-order/retried delivery is handled:
  * duplicate: the DB unique constraint on stripe_event_id makes a
    redelivered event a no-op (see repository/donations/webhook_events.py).
  * out-of-order: every donation/ledger mutation here checks current state
    before transitioning (e.g. a succeeded->failed pair arriving swapped
    can't un-succeed a donation), and ledger inserts are keyed by
    (donation_id, movement_type, stripe_object_id) so replays/re-deliveries
    of the same fact are idempotent.
  * processing errors: caught per-event by the Flask route (see
    api/donations/webhooks.py), which marks the StripeWebhookEvent FAILED
    with the error and still 200s so Stripe doesn't hot-loop retries on a
    bug we've already durably logged.

Webhook-confirmed events are the source of truth — nothing here is ever
inferred from a Checkout Session redirect.
"""
import domain.donations.limits as limits_domain
import repository.donations.accounts as accounts_data
import repository.donations.donations as donations_data
import repository.donations.funding_needs as funding_needs_data
import repository.donations.ledger as ledger_data
import repository.donations.payment_profiles as profiles_data
from stripe_connect.service import get_charge_with_balance_transaction, retrieve_payment_method
from utils.logger import logger

DISPUTE_STATUS_MAP = {
	"won": "WON",
	"lost": "LOST",
}


def _donation_for_payment_intent(payment_intent_id, metadata=None):
	donation = donations_data.get_donation_by_payment_intent(payment_intent_id)
	if donation:
		return donation
	donation_id = (metadata or {}).get("donation_id")
	if donation_id:
		return donations_data.get_donation(donation_id)
	return None


def handle_payment_intent_processing(payment_intent):
	donation = _donation_for_payment_intent(payment_intent["id"], payment_intent.get("metadata"))
	if not donation:
		logger.warning(f"payment_intent.processing: no donation found for {payment_intent['id']}")
		return
	donations_data.mark_processing(donation.id, payment_intent["id"])


def handle_payment_intent_succeeded(payment_intent, stripe_account_id):
	donation = _donation_for_payment_intent(payment_intent["id"], payment_intent.get("metadata"))
	if not donation:
		logger.warning(f"payment_intent.succeeded: no donation found for {payment_intent['id']}")
		return
	if donation.status.name == "SUCCEEDED":
		return  # already processed (redelivery)

	charge_id = payment_intent.get("latest_charge")
	processing_fee_cents = 0
	if charge_id and stripe_account_id:
		try:
			charge = get_charge_with_balance_transaction(stripe_account_id, charge_id)
			bt = getattr(charge, "balance_transaction", None)
			processing_fee_cents = getattr(bt, "fee", 0) or 0
		except Exception as e:
			logger.error(f"failed to fetch balance_transaction for charge {charge_id}: {e}")

	shelter_net_cents = donation.gross_amount_cents - donation.platform_fee_amount_cents - processing_fee_cents

	donations_data.mark_succeeded(
		donation.id, processing_fee_amount_cents=processing_fee_cents,
		shelter_net_amount_cents=shelter_net_cents, stripe_payment_intent_id=payment_intent["id"],
	)

	pi_id = payment_intent["id"]
	ledger_data.record_movement(
		shelter_id=donation.shelter_id, movement_type="GROSS_PAYMENT",
		amount_cents=donation.gross_amount_cents, donation_id=donation.id,
		stripe_object_id=pi_id, currency=donation.currency, is_test=donation.is_test,
	)
	ledger_data.record_movement(
		shelter_id=donation.shelter_id, movement_type="PLATFORM_FEE",
		amount_cents=-donation.platform_fee_amount_cents, donation_id=donation.id,
		stripe_object_id=pi_id, currency=donation.currency, is_test=donation.is_test,
	)
	ledger_data.record_movement(
		shelter_id=donation.shelter_id, movement_type="PROCESSING_FEE",
		amount_cents=-processing_fee_cents, donation_id=donation.id,
		stripe_object_id=pi_id, currency=donation.currency, is_test=donation.is_test,
	)
	ledger_data.record_movement(
		shelter_id=donation.shelter_id, movement_type="SHELTER_NET",
		amount_cents=-shelter_net_cents, donation_id=donation.id,
		stripe_object_id=pi_id, currency=donation.currency, is_test=donation.is_test,
	)

	if donation.reservation_id:
		limits_domain.consume_reservation(donation.reservation_id, donation.id)
	if donation.funding_need_id:
		funding_needs_data.increment_collected_amount(donation.funding_need_id, donation.gross_amount_cents)

	_notify_shelter_members_of_donation(donation)


def _notify_shelter_members_of_donation(donation):
	"""Every shelter member with an account gets a DONATION_RECEIVED
	notification (amount + pet vs shelter target). Failures are swallowed:
	a notification bug must never fail the financial webhook processing.
	Imports are function-level to keep this module free of domain-package
	import cycles. Idempotent per donation+member via dedupe_key, so a
	webhook redelivery can't double-notify."""
	try:
		import domain.notifications as notifications_domain
		import repository.pets as pets_data
		import repository.shelters as shelters_data

		shelter = shelters_data.get_shelter(donation.shelter_id) or {}
		pet_name = None
		if donation.pet_id:
			try:
				pet = pets_data.get_pet(donation.pet_id) or {}
				pet_name = pet.get("name")
			except Exception:
				pet_name = None

		import repository.authorization as authz_data
		member_user_ids = authz_data.get_active_member_user_ids(donation.shelter_id)
		for member_user_id in member_user_ids:
			notifications_domain.notify_donation_received(
				donation_id=donation.id,
				user_id=member_user_id,
				shelter_id=donation.shelter_id,
				shelter_name=shelter.get("name"),
				amount_cents=donation.gross_amount_cents,
				currency=donation.currency,
				pet_name=pet_name,
				is_test=donation.is_test,
			)
	except Exception as e:
		logger.error(f"failed to notify shelter members for donation {donation.id}: {e}")


def handle_payment_intent_failed(payment_intent):
	donation = _donation_for_payment_intent(payment_intent["id"], payment_intent.get("metadata"))
	if not donation:
		logger.warning(f"payment_intent.payment_failed: no donation found for {payment_intent['id']}")
		return
	if donation.status.name in ("SUCCEEDED", "FAILED"):
		return
	donations_data.mark_failed(donation.id)
	if donation.reservation_id:
		limits_domain.release_reservation(donation.reservation_id)


def handle_payment_intent_canceled(payment_intent):
	donation = _donation_for_payment_intent(payment_intent["id"], payment_intent.get("metadata"))
	if not donation:
		logger.warning(f"payment_intent.canceled: no donation found for {payment_intent['id']}")
		return
	if donation.status.name in ("SUCCEEDED", "CANCELED"):
		return
	donations_data.mark_canceled(donation.id)
	if donation.reservation_id:
		limits_domain.release_reservation(donation.reservation_id)


def handle_charge_refunded(charge):
	donation = donations_data.get_donation_by_payment_intent(charge.get("payment_intent"))
	if not donation:
		logger.warning(f"charge.refunded: no donation found for payment_intent {charge.get('payment_intent')}")
		return

	refunds = (charge.get("refunds") or {}).get("data", [])
	total_refunded = charge.get("amount_refunded", 0)
	full = total_refunded >= donation.gross_amount_cents

	for refund in refunds:
		_, created = ledger_data.record_movement(
			shelter_id=donation.shelter_id, movement_type="REFUND",
			amount_cents=-refund["amount"], donation_id=donation.id,
			stripe_object_id=refund["id"], currency=donation.currency, is_test=donation.is_test,
		)
		if created:
			# the refunded amount also leaves the shelter's net position —
			# a compensating movement, not an edit to the original SHELTER_NET row
			ledger_data.record_movement(
				shelter_id=donation.shelter_id, movement_type="ADJUSTMENT",
				amount_cents=refund["amount"], donation_id=donation.id,
				stripe_object_id=f"{refund['id']}:shelter_adjustment",
				currency=donation.currency, is_test=donation.is_test,
				description="compensates REFUND against SHELTER_NET",
			)

	donations_data.apply_refund(donation.id, total_refunded, full)
	if donation.reservation_id:
		limits_domain.release_reservation_on_refund(
			donation.reservation_id, total_refunded, donation.gross_amount_cents,
		)


def handle_charge_dispute(dispute):
	donation = donations_data.get_donation_by_payment_intent(dispute.get("payment_intent"))
	if not donation:
		logger.warning(f"charge.dispute.*: no donation found for payment_intent {dispute.get('payment_intent')}")
		return

	status = DISPUTE_STATUS_MAP.get(dispute.get("status"), "OPEN")
	donations_data.set_dispute_status(donation.id, status)

	ledger_data.record_movement(
		shelter_id=donation.shelter_id, movement_type="DISPUTE",
		amount_cents=-dispute["amount"], donation_id=donation.id,
		stripe_object_id=dispute["id"], currency=donation.currency, is_test=donation.is_test,
	)
	if status == "WON":
		ledger_data.record_movement(
			shelter_id=donation.shelter_id, movement_type="REVERSAL",
			amount_cents=dispute["amount"], donation_id=donation.id,
			stripe_object_id=f"{dispute['id']}:won_reversal",
			currency=donation.currency, is_test=donation.is_test,
		)


def handle_account_updated(account):
	connected_account = accounts_data.get_connected_account_by_stripe_id(account["id"])
	if not connected_account:
		return
	merchant = (account.get("configuration") or {}).get("merchant") or {}
	card_payments_status = ((merchant.get("capabilities") or {}).get("card_payments") or {}).get("status")
	accounts_data.update_account_status(
		connected_account.id,
		charges_enabled=(card_payments_status == "active"),
		payouts_enabled=bool(account.get("payouts_enabled", connected_account.payouts_enabled)),
		details_submitted=bool(account.get("details_submitted", connected_account.details_submitted)),
	)


def handle_payout(payout, stripe_account_id, event_type):
	if not stripe_account_id:
		logger.warning(f"{event_type}: no connected account id on event, skipping ledger entry")
		return
	connected_account = accounts_data.get_connected_account_by_stripe_id(stripe_account_id)
	if not connected_account:
		return
	status_suffix = event_type.split(".")[-1]  # created | paid | failed
	ledger_data.record_movement(
		shelter_id=connected_account.shelter_id, movement_type="PAYOUT",
		amount_cents=-payout["amount"] if status_suffix != "failed" else 0,
		stripe_object_id=f"{payout['id']}:{status_suffix}",
		currency=payout.get("currency", "usd"),
		description=f"payout {status_suffix}",
		is_test=not payout.get("livemode", False),
	)


def handle_setup_intent_succeeded(setup_intent):
	"""See module docstring: this is the only place a saved payment method
	actually gets persisted, since the task's mutation list has no
	confirm-setup mutation. `user_id`/`consent_text` were stashed in
	metadata when the Checkout Session was created (see
	domain/donations/payment_methods.create_payment_method_setup)."""
	metadata = setup_intent.get("metadata") or {}
	user_id = metadata.get("user_id")
	consent_text = metadata.get("consent_text")
	payment_method_id = setup_intent.get("payment_method")
	if not user_id or not payment_method_id:
		logger.warning(f"setup_intent.succeeded {setup_intent.get('id')}: missing user_id/payment_method")
		return

	profile = profiles_data.get_profile_for_user(user_id)
	if not profile:
		logger.warning(f"setup_intent.succeeded {setup_intent.get('id')}: no payment profile for user {user_id}")
		return

	try:
		pm = retrieve_payment_method(payment_method_id)
	except Exception as e:
		logger.error(f"failed to retrieve payment method {payment_method_id}: {e}")
		return

	card = getattr(pm, "card", None)
	model = profiles_data.create_payment_method(
		profile.id, payment_method_id,
		card_brand=getattr(card, "brand", None) if card else None,
		card_last4=getattr(card, "last4", None) if card else None,
		card_exp_month=getattr(card, "exp_month", None) if card else None,
		card_exp_year=getattr(card, "exp_year", None) if card else None,
	)
	if consent_text:
		profiles_data.record_consent(model.id, consent_text)


HANDLERS = {
	"payment_intent.processing": lambda obj, account: handle_payment_intent_processing(obj),
	"payment_intent.succeeded": lambda obj, account: handle_payment_intent_succeeded(obj, account),
	"payment_intent.payment_failed": lambda obj, account: handle_payment_intent_failed(obj),
	"payment_intent.canceled": lambda obj, account: handle_payment_intent_canceled(obj),
	"charge.refunded": lambda obj, account: handle_charge_refunded(obj),
	"charge.dispute.created": lambda obj, account: handle_charge_dispute(obj),
	"charge.dispute.updated": lambda obj, account: handle_charge_dispute(obj),
	"charge.dispute.closed": lambda obj, account: handle_charge_dispute(obj),
	"account.updated": lambda obj, account: handle_account_updated(obj),
	"setup_intent.succeeded": lambda obj, account: handle_setup_intent_succeeded(obj),
}


def process_event(event_type, event_object, stripe_account_id=None):
	if event_type.startswith("payout."):
		handle_payout(event_object, stripe_account_id, event_type)
		return
	handler = HANDLERS.get(event_type)
	if handler is None:
		logger.info(f"donation webhook: unhandled event type {event_type}")
		return
	handler(event_object, stripe_account_id)
