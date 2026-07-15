"""Platform-scoped donation operations (PLATFORM_ADMIN /
PLATFORM_FINANCE_OPERATOR): cross-shelter donation/ledger/dispute/webhook
visibility, refunds, connected account listing, and reconciliation.

Refunds/reconciliation trigger the Stripe-side action and return
immediately; the actual ledger booking always happens from the
webhook-confirmed event (see domain/donations/webhooks.py) — this module
never writes FinancialMovement rows itself, per "webhook-confirmed events
are the source of truth".
"""
from api.errors import NotFoundError, BadRequest
import repository.donations.accounts as accounts_data
import repository.donations.donations as donations_data
import repository.donations.ledger as ledger_data
import repository.donations.webhook_events as webhook_events_data
from stripe_connect import get_environment
from stripe_connect.service import create_refund


def list_platform_donations(page=0, page_size=20, shelter_id=None, status=None, donor_type=None,
							 order_by="created_at", order_direction="desc"):
	items, total = donations_data.list_donations_platform(
		page=page, page_size=page_size, shelter_id=shelter_id, status=status, donor_type=donor_type,
		order_by=order_by, order_direction=order_direction,
	)
	return [d.to_dict() for d in items], total


def _get_donation_and_account(donation_id):
	donation = donations_data.get_donation(donation_id)
	if donation is None:
		raise NotFoundError(f"no donation found with id {donation_id}")
	account = accounts_data.get_connected_account_by_id(donation.connected_account_id)
	if account is None:
		raise NotFoundError("connected account for this donation no longer exists")
	return donation, account


def refund_donation(donation_id, reason=None):
	donation, account = _get_donation_and_account(donation_id)
	if donation.status.name != "SUCCEEDED":
		raise BadRequest(f"cannot refund a donation in status {donation.status.name}")
	if not donation.stripe_payment_intent_id:
		raise BadRequest("donation has no payment_intent to refund")
	create_refund(account.stripe_account_id, donation.stripe_payment_intent_id, refund_application_fee=True)
	return donations_data.get_donation(donation_id).to_dict()


def partially_refund_donation(donation_id, amount_cents, reason):
	if not reason or not reason.strip():
		raise BadRequest("a reason is required for a partial refund")
	donation, account = _get_donation_and_account(donation_id)
	if donation.status.name != "SUCCEEDED":
		raise BadRequest(f"cannot refund a donation in status {donation.status.name}")
	if not isinstance(amount_cents, int) or amount_cents <= 0 or amount_cents >= donation.gross_amount_cents:
		raise BadRequest("amount_cents must be a positive integer smaller than the gross donation amount")
	if not donation.stripe_payment_intent_id:
		raise BadRequest("donation has no payment_intent to refund")
	create_refund(account.stripe_account_id, donation.stripe_payment_intent_id, amount_cents=amount_cents)
	return donations_data.get_donation(donation_id).to_dict()


def list_disputes(page=0, page_size=20):
	"""Disputed donations are just Donations with dispute_status != NONE —
	no separate Dispute model exists (not in the task's fixed 10-model
	list); see docs/donations-backend.md for this design note."""
	items, total = donations_data.list_donations_platform(page=page, page_size=page_size)
	disputed = [d.to_dict() for d in items if d.dispute_status.name != "NONE"]
	return disputed, total


def list_connected_accounts(environment=None):
	return [a.to_dict() for a in accounts_data.list_connected_accounts(environment)]


def suspend_connected_account(connected_account_id):
	account = accounts_data.get_connected_account_by_id(connected_account_id)
	if account is None:
		raise NotFoundError(f"no connected account found with id {connected_account_id}")
	return accounts_data.set_donations_enabled(connected_account_id, False).to_dict()


def list_financial_movements(page=0, page_size=50, shelter_id=None, movement_type=None):
	items, total = ledger_data.list_movements_platform(
		page=page, page_size=page_size, shelter_id=shelter_id, movement_type=movement_type,
	)
	return [m.to_dict() for m in items], total


def reconcile_financial_transaction(donation_id):
	"""Read-only reconciliation check for now: reports whether a
	donation's movements balance to zero (see
	repository/donations/ledger.is_balanced). Does not (and, with Direct
	Charges settling automatically, generally should not need to) write
	an adjustment — a real discrepancy would come from a Stripe balance
	transaction reconciliation job, out of scope here."""
	donation = donations_data.get_donation(donation_id)
	if donation is None:
		raise NotFoundError(f"no donation found with id {donation_id}")
	movements = ledger_data.list_movements_for_donation(donation_id)
	return {
		"donation_id": donation_id,
		"is_balanced": ledger_data.is_balanced(donation_id),
		"movement_count": len(movements),
	}


def list_stripe_webhook_events(page=0, page_size=50, status=None, event_type=None):
	items, total = webhook_events_data.list_events(page=page, page_size=page_size, status=status,
													event_type=event_type)
	return [e.to_dict() for e in items], total


def retry_stripe_webhook_event(event_id):
	"""Re-runs the SAME processing this event went through on first
	delivery — safe because every handler in domain/donations/webhooks.py
	is idempotent (state-checked donation transitions, unique-keyed ledger
	inserts). Rejects retrying a livemode=true event while in test mode,
	same guard as first-time processing."""
	event = webhook_events_data.get_event(event_id)
	if event is None:
		raise NotFoundError(f"no webhook event found with id {event_id}")
	if event.livemode and get_environment() == "test":
		raise BadRequest("refusing to retry a livemode=true event while running in test mode")

	import domain.donations.webhooks as webhooks_domain
	try:
		payload = event.payload or {}
		event_object = (payload.get("data") or {}).get("object", {})
		account_id = payload.get("account")
		webhooks_domain.process_event(event.event_type, event_object, account_id)
		webhook_events_data.mark_processed(event.id)
	except Exception as e:
		webhook_events_data.mark_failed(event.id, str(e))
		raise
	return webhook_events_data.get_event(event_id).to_dict()
