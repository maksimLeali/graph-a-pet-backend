"""Shelter donation overview + monthly report aggregation.

Every total here comes from `FinancialMovement` (webhook-confirmed ledger
rows) or straightforward DB counts — never estimated from a Checkout
redirect, per the task's "Do not calculate authoritative totals from
Stripe Checkout redirects" rule.
"""
from datetime import datetime

import domain.shelters as shelters_domain
import domain.donations.limits as limits_domain
import repository.donations.accounts as accounts_data
import repository.donations.expenses as expenses_data
import repository.donations.funding_needs as funding_needs_data
import repository.donations.ledger as ledger_data
import repository.donations.shelter_pets as shelter_pets_data
from stripe_connect import get_environment

NEAR_LIMIT_THRESHOLD_RATIO = 0.1  # remaining <= 10% of the limit counts as "near"


def _pets_near_or_at_limit(shelter_id, shelter_timezone):
	near, at = 0, 0
	for shelter_pet in shelter_pets_data.list_published_shelter_pets(shelter_id):
		allowance = limits_domain.get_remaining_allowance_cents(shelter_pet.pet_id, shelter_id, shelter_timezone)
		if allowance["limit_cents"] <= 0:
			continue
		if allowance["remaining_cents"] <= 0:
			at += 1
		elif allowance["remaining_cents"] <= allowance["limit_cents"] * NEAR_LIMIT_THRESHOLD_RATIO:
			near += 1
	return near, at


def get_shelter_donation_overview(shelter_id):
	shelter = shelters_domain.get_shelter(shelter_id)  # raises NotFoundError if missing
	totals = ledger_data.sum_by_type(shelter_id)

	gross = totals.get("GROSS_PAYMENT", 0)
	platform_fees = -totals.get("PLATFORM_FEE", 0)
	processing_fees = -totals.get("PROCESSING_FEE", 0)
	shelter_net = -totals.get("SHELTER_NET", 0)
	refunds = -totals.get("REFUND", 0)
	disputes = -totals.get("DISPUTE", 0)
	payouts = -totals.get("PAYOUT", 0)

	declared_expenses = sum(
		e.amount_cents for e in expenses_data.list_expenses_for_shelter(shelter_id, status="APPROVED")
	)
	unreported_cents = max(shelter_net - refunds - declared_expenses - payouts, 0)

	active_funding_needs = len(funding_needs_data.list_funding_needs(shelter_id, status="ACTIVE"))
	near_limit, at_limit = _pets_near_or_at_limit(shelter_id, shelter.get("timezone") or "UTC")

	account = accounts_data.get_active_connected_account(shelter_id, get_environment().upper())

	return {
		"gross_amount_cents": gross,
		"platform_fee_amount_cents": platform_fees,
		"processing_fee_amount_cents": processing_fees,
		"shelter_net_amount_cents": shelter_net,
		"refunded_amount_cents": refunds,
		"disputed_amount_cents": disputes,
		"declared_expenses_cents": declared_expenses,
		"unreported_funds_cents": unreported_cents,
		"active_funding_needs_count": active_funding_needs,
		"pets_near_limit_count": near_limit,
		"pets_at_limit_count": at_limit,
		"connected_account": account.to_dict() if account else None,
		"is_test_mode": get_environment() == "test",
	}


def get_shelter_monthly_report(shelter_id, year, month):
	shelters_domain.get_shelter(shelter_id)  # raises NotFoundError if missing
	start = datetime(year, month, 1)
	end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

	totals = ledger_data.sum_by_type(shelter_id, start=start, end=end)
	gross = totals.get("GROSS_PAYMENT", 0)
	platform_fees = -totals.get("PLATFORM_FEE", 0)
	processing_fees = -totals.get("PROCESSING_FEE", 0)
	shelter_net = -totals.get("SHELTER_NET", 0)
	refunds = -totals.get("REFUND", 0)
	disputes = -totals.get("DISPUTE", 0)

	declared_expenses = sum(
		e.amount_cents for e in expenses_data.list_expenses_for_shelter(shelter_id, status="APPROVED")
		if e.approved_at and start <= e.approved_at < end
	)
	unreported_cents = max(shelter_net - refunds - declared_expenses, 0)

	return {
		"year": year,
		"month": month,
		"gross_amount_cents": gross,
		"platform_fee_amount_cents": platform_fees,
		"processing_fee_amount_cents": processing_fees,
		"shelter_net_amount_cents": shelter_net,
		"refunded_amount_cents": refunds,
		"disputed_amount_cents": disputes,
		"declared_expenses_cents": declared_expenses,
		"unreported_funds_cents": unreported_cents,
	}
