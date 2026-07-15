"""Authenticated donor saved payment methods.

Donors are never Stripe Connect accounts — they get a plain platform-level
Stripe Customer (`UserPaymentProfile.stripe_customer_id`), separate from
any shelter's connected account. Only masked display fields
(brand/last4/exp) are ever persisted — never a full card number or CVC,
which Stripe itself never returns to a server integration anyway.

`createPaymentMethodSetup` redirects the donor to Stripe-hosted Checkout in
`setup` mode; the resulting `setup_intent.succeeded` webhook (see
domain/donations/webhooks.py — added to the webhook set beyond the task's
minimum list specifically to close this loop, since there is no
`confirmPaymentMethodSetup` mutation in the task's spec) is what actually
persists the UserPaymentMethod + PaymentMethodConsent rows.
"""
from api.errors import BadRequest, NotFoundError
import repository.donations.payment_profiles as profiles_data
from stripe_connect.service import create_customer, create_setup_checkout_session, detach_payment_method


def _get_or_create_profile(user_id, user_email):
	profile = profiles_data.get_profile_for_user(user_id)
	if profile:
		return profile
	customer = create_customer(user_email)
	return profiles_data.create_profile(user_id, customer.id)


def create_payment_method_setup(user_id, user_email, success_url, cancel_url, consent_text):
	if not consent_text or not consent_text.strip():
		raise BadRequest("consent_text is required to save a payment method")
	profile = _get_or_create_profile(user_id, user_email)
	session = create_setup_checkout_session(
		profile.stripe_customer_id, success_url, cancel_url, user_id, consent_text.strip(),
	)
	return {"setup_url": session.url}


def list_payment_methods(user_id):
	profile = profiles_data.get_profile_for_user(user_id)
	if not profile:
		return []
	return [pm.to_dict() for pm in profiles_data.list_payment_methods(profile.id)]


def remove_payment_method(user_id, user_payment_method_id):
	profile = profiles_data.get_profile_for_user(user_id)
	pm = profiles_data.get_payment_method(user_payment_method_id) if profile else None
	if not profile or not pm or pm.user_payment_profile_id != profile.id:
		raise NotFoundError("no saved payment method found for this user")

	try:
		detach_payment_method(pm.stripe_payment_method_id)
	except Exception:
		pass  # already detached/gone on Stripe's side — still remove our record

	profiles_data.deactivate_payment_method(user_payment_method_id)
	if profile.default_payment_method_id == user_payment_method_id:
		profiles_data.set_default_payment_method(profile.id, None)
	return True


def set_default_payment_method(user_id, user_payment_method_id):
	profile = profiles_data.get_profile_for_user(user_id)
	pm = profiles_data.get_payment_method(user_payment_method_id) if profile else None
	if not profile or not pm or pm.user_payment_profile_id != profile.id or not pm.is_active:
		raise NotFoundError("no saved payment method found for this user")
	updated = profiles_data.set_default_payment_method(profile.id, user_payment_method_id)
	return updated.to_dict()
