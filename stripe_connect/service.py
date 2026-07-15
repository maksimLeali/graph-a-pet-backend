"""Stripe API call wrappers. Every call goes through the single
`get_stripe_client()` StripeClient (see stripe_connect/__init__.py) — no ad
hoc `stripe.Product.create(...)`-style top-level calls anywhere.

Field shapes here were verified against the installed `stripe==15.3.0`
python SDK's generated param TypedDicts (`stripe/params/v2/core/...py`) —
not guessed from the JS examples in the task.
"""
from stripe_connect import get_stripe_client


# ---------------------------------------------------------------------------
# Connected accounts (V2 Accounts API)
# ---------------------------------------------------------------------------

def create_connected_account(display_name: str, contact_email: str):
	"""Create a V2 connected account.

	Only the properties explicitly given in the task are used. In
	particular there is NO top-level `type` field — V2 accounts are
	configured entirely through `configuration`/`defaults`/`identity`, never
	'express' | 'standard' | 'custom'.
	"""
	client = get_stripe_client()
	return client.v2.core.accounts.create({
		"display_name": display_name,
		"contact_email": contact_email,
		"identity": {
			# PLACEHOLDER: hardcoded to 'us' for this demo. A real
			# integration would collect the seller's actual country.
			"country": "us",
		},
		"dashboard": "full",
		"defaults": {
			"responsibilities": {
				"fees_collector": "stripe",
				"losses_collector": "stripe",
			},
		},
		"configuration": {
			"customer": {},
			"merchant": {
				"capabilities": {
					"card_payments": {
						"requested": True,
					},
				},
			},
		},
	})


def get_account_status(stripe_account_id: str):
	"""Always fetched live from the Accounts API — per the task, this demo
	never stores/caches onboarding or capability status in the DB, only the
	`stripe_account_id` mapping itself (see stripe_connect/data.py)."""
	client = get_stripe_client()
	account = client.v2.core.accounts.retrieve(
		stripe_account_id,
		{"include": ["configuration.merchant", "requirements"]},
	)

	merchant = getattr(account.configuration, "merchant", None) if account.configuration else None
	card_payments = getattr(merchant.capabilities, "card_payments", None) if merchant and merchant.capabilities else None
	ready_to_process_payments = bool(card_payments and card_payments.status == "active")

	requirements_status = None
	if account.requirements and account.requirements.summary and account.requirements.summary.minimum_deadline:
		requirements_status = account.requirements.summary.minimum_deadline.status

	onboarding_complete = requirements_status not in ("currently_due", "past_due")

	# Human-readable outstanding-requirement descriptions (V2's `entries`
	# replaces V1's flat `currently_due`/`past_due` string-code lists).
	requirements = [
		entry.description
		for entry in (account.requirements.entries if account.requirements else []) or []
	]

	return {
		"account": account,
		"ready_to_process_payments": ready_to_process_payments,
		"onboarding_complete": onboarding_complete,
		"requirements_status": requirements_status,
		"requirements": requirements,
	}


def create_onboarding_account_link(stripe_account_id: str, refresh_url: str, return_url: str):
	client = get_stripe_client()
	return client.v2.core.account_links.create({
		"account": stripe_account_id,
		"use_case": {
			"type": "account_onboarding",
			"account_onboarding": {
				"configurations": ["merchant", "customer"],
				"refresh_url": refresh_url,
				"return_url": return_url,
			},
		},
	})


# ---------------------------------------------------------------------------
# Products (created/listed ON the connected account via the Stripe-Account
# header — passed as `{"stripe_account": ...}` request options in python)
# ---------------------------------------------------------------------------

def create_product(stripe_account_id: str, name: str, description: str, price_in_cents: int,
					currency: str = "usd"):
	client = get_stripe_client()
	return client.v1.products.create(
		{
			"name": name,
			"description": description,
			"default_price_data": {
				"unit_amount": price_in_cents,
				"currency": currency,
			},
		},
		{"stripe_account": stripe_account_id},
	)


def list_products(stripe_account_id: str):
	client = get_stripe_client()
	return client.v1.products.list(
		{
			"limit": 20,
			"active": True,
			"expand": ["data.default_price"],
		},
		{"stripe_account": stripe_account_id},
	)


# ---------------------------------------------------------------------------
# Direct charge checkout (storefront purchase) — Direct Charge + application
# fee, per the task. Hosted Checkout for simplicity.
# ---------------------------------------------------------------------------

def create_direct_charge_checkout_session(stripe_account_id: str, price_id: str,
										   success_url: str, application_fee_amount: int):
	"""SAMPLE-ONLY (fixed catalog `price_id`, storefront demo). The real
	donation checkout uses `create_donation_checkout_session` below, which
	takes an arbitrary donor-entered amount via `price_data` instead of a
	pre-created Price."""
	client = get_stripe_client()
	return client.v1.checkout.sessions.create(
		{
			"line_items": [
				{"price": price_id, "quantity": 1},
			],
			"payment_intent_data": {
				"application_fee_amount": application_fee_amount,
			},
			"mode": "payment",
			"success_url": success_url,
		},
		{"stripe_account": stripe_account_id},
	)


def create_donation_checkout_session(stripe_account_id: str, amount_cents: int, currency: str,
									  product_name: str, application_fee_amount: int,
									  success_url: str, donation_id: str, customer_email: str = None):
	"""Real donation checkout — Direct Charge (created on the connected
	account via the `stripe_account` request option, same mechanism as the
	sample above) + application fee, but with an ad hoc `price_data` line
	item since a donation amount is whatever the donor typed in, not a
	pre-created catalog Price. Used by domain/donations/checkout.py for
	both guest and authenticated donations.

	`payment_intent_data.metadata.donation_id` is how
	domain/donations/webhooks.py links a payment_intent.* webhook event
	back to our own Donation row — the task's webhook list has no
	checkout.session.completed event, so the PaymentIntent itself must
	carry this reference.
	"""
	client = get_stripe_client()
	params = {
		"line_items": [
			{
				"price_data": {
					"currency": currency,
					"unit_amount": amount_cents,
					"product_data": {"name": product_name},
				},
				"quantity": 1,
			},
		],
		"payment_intent_data": {
			"application_fee_amount": application_fee_amount,
			"metadata": {"donation_id": donation_id},
		},
		"mode": "payment",
		"success_url": success_url,
	}
	if customer_email:
		params["customer_email"] = customer_email
	return client.v1.checkout.sessions.create(params, {"stripe_account": stripe_account_id})


def create_refund(stripe_account_id: str, payment_intent_id: str, amount_cents: int = None,
				   refund_application_fee: bool = False):
	"""Full refund when `amount_cents` is None, partial otherwise. Created
	on the connected account (Direct Charge) via the `stripe_account`
	option — same as every other charge-side call in this module. The
	`charge.refunded` webhook (domain/donations/webhooks.py) is what
	actually books the ledger movements; this call only triggers Stripe's
	side, it never writes Donation/FinancialMovement rows itself."""
	client = get_stripe_client()
	params = {"payment_intent": payment_intent_id, "refund_application_fee": refund_application_fee}
	if amount_cents is not None:
		params["amount"] = amount_cents
	return client.v1.refunds.create(params, {"stripe_account": stripe_account_id})


def create_customer(email: str):
	"""Platform-level Customer — donors are never connected accounts, so
	this is a plain v1 call with no `stripe_account` option."""
	client = get_stripe_client()
	return client.v1.customers.create({"email": email})


def create_setup_checkout_session(customer_id: str, success_url: str, cancel_url: str,
								   user_id: str, consent_text: str):
	"""Hosted Checkout in `setup` mode — the donor is redirected to a
	Stripe-hosted page to add a card with no charge attached. The
	resulting SetupIntent's metadata carries `user_id`/`consent_text` so
	domain/donations/webhooks.py can persist the UserPaymentMethod +
	PaymentMethodConsent together once `setup_intent.succeeded` fires."""
	client = get_stripe_client()
	return client.v1.checkout.sessions.create({
		"customer": customer_id,
		"mode": "setup",
		"success_url": success_url,
		"cancel_url": cancel_url,
		"setup_intent_data": {
			"metadata": {"user_id": user_id, "consent_text": consent_text},
		},
	})


def retrieve_payment_method(payment_method_id: str):
	client = get_stripe_client()
	return client.v1.payment_methods.retrieve(payment_method_id)


def detach_payment_method(payment_method_id: str):
	client = get_stripe_client()
	return client.v1.payment_methods.detach(payment_method_id)


def get_charge_with_balance_transaction(stripe_account_id: str, charge_id: str):
	"""The real Stripe processing fee only exists on the balance
	transaction (not the PaymentIntent/Charge payload itself) — used by
	domain/donations/webhooks.py on payment_intent.succeeded to record the
	true PROCESSING_FEE ledger movement instead of estimating it."""
	client = get_stripe_client()
	return client.v1.charges.retrieve(
		charge_id, {"expand": ["balance_transaction"]}, {"stripe_account": stripe_account_id},
	)


# ---------------------------------------------------------------------------
# SAMPLE-ONLY from here down — subscribing a connected account to a
# platform-level plan, and its billing portal. Explicitly OUT of scope for
# the real donation domain (donations have no subscription concept); kept
# only so the isolated stripe_connect/ sample stays runnable when
# SAMPLE_ENABLED is manually flipped on. V2 accounts are their own
# customer — `customer_account`, never `customer`, and this checkout
# session is created WITHOUT a `stripe_account` request option (it's a
# platform-level object, not something created on/for the connected
# account itself).
# ---------------------------------------------------------------------------

def create_platform_subscription_checkout_session(stripe_account_id: str, price_id: str,
													success_url: str, cancel_url: str):
	client = get_stripe_client()
	return client.v1.checkout.sessions.create({
		"customer_account": stripe_account_id,
		"mode": "subscription",
		"line_items": [
			{"price": price_id, "quantity": 1},
		],
		"success_url": success_url,
		"cancel_url": cancel_url,
	})


def create_billing_portal_session(stripe_account_id: str, return_url: str):
	client = get_stripe_client()
	return client.v1.billing_portal.sessions.create({
		"customer_account": stripe_account_id,
		"return_url": return_url,
	})
