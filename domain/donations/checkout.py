"""Guest and authenticated donation checkout creation.

Both flows share the exact same validation + Stripe Direct Charge Checkout
Session creation — the only difference is donor identity (guest: email
required, no account; authenticated: donor_user_id set from the caller's
JWT). See api/donations/mutations.py for how the two GraphQL mutations
differ only in how they resolve donor identity before calling
`create_donation_checkout` here.

A payment must never be created past a pet's remaining monthly allowance:
for PET-targeted donations, the allowance is reserved (see
domain/donations/limits.reserve_pet_allowance, which raises
DonationExceedsPetLimitError) BEFORE the Checkout Session is created.
"""
from api.errors import BadRequest, InvalidDonationAmountError
import domain.donations.public as public_domain
import domain.donations.limits as limits_domain
import domain.shelters as shelters_domain
import repository.donations.accounts as accounts_data
import repository.donations.donations as donations_data
from stripe_connect import get_environment, get_platform_fee_percent
from stripe_connect.service import create_donation_checkout_session

# arbitrary but sane floor against fat-fingered/zero donations
MIN_AMOUNT_CENTS = 100

PRODUCT_NAME_BY_TARGET = {
	"SHELTER": "Donation",
	"PET": "Pet donation",
	"PET_FUNDING_NEED": "Funding need donation",
}


def _validate_amount(amount_cents):
	if not isinstance(amount_cents, int) or isinstance(amount_cents, bool) or amount_cents < MIN_AMOUNT_CENTS:
		raise InvalidDonationAmountError(
			f"donation amount must be an integer of at least {MIN_AMOUNT_CENTS} cents"
		)


def _append_redirect_params(success_url, donation_id):
	"""The app's pending-confirmation page (DonationPendingPage) needs the
	donation_id to know what to poll — it can't be known by the caller
	before this call creates the donation, so the backend injects it here,
	same as the Stripe-provided session_id placeholder."""
	separator = "&" if "?" in success_url else "?"
	return f"{success_url}{separator}donation_id={donation_id}&session_id={{CHECKOUT_SESSION_ID}}"


def create_donation_checkout(*, shelter_id, target_type, amount_cents, success_url,
							  currency="usd", pet_id=None, funding_need_id=None,
							  donor_user_id=None, donor_email=None):
	_validate_amount(amount_cents)

	if target_type == "PET" and not pet_id:
		raise BadRequest("pet_id is required when target_type is PET")
	if target_type == "PET_FUNDING_NEED" and not funding_need_id:
		raise BadRequest("funding_need_id is required when target_type is PET_FUNDING_NEED")
	if not donor_user_id and not donor_email:
		raise BadRequest("donor_email is required for guest donations")

	availability = public_domain.get_public_donation_availability(
		shelter_id, pet_id=pet_id, funding_need_id=funding_need_id,
	)
	if not availability["available"]:
		raise BadRequest(f"donation not available: {', '.join(availability['reasons'])}")

	# availability["available"] guarantees an active connected account exists
	account = accounts_data.get_active_connected_account(shelter_id, get_environment().upper())

	reservation = None
	if target_type == "PET":
		shelter = shelters_domain.get_shelter(shelter_id)
		reservation = limits_domain.reserve_pet_allowance(
			pet_id, shelter_id, shelter.get("timezone") or "UTC", amount_cents,
		)

	donor_type = "AUTHENTICATED" if donor_user_id else "GUEST"
	platform_fee_percent = get_platform_fee_percent()

	donation = donations_data.create_pending_donation(
		shelter_id=shelter_id, connected_account_id=account.id, target_type=target_type,
		donor_type=donor_type, gross_amount_cents=amount_cents,
		platform_fee_percent=platform_fee_percent, currency=currency,
		pet_id=pet_id, funding_need_id=funding_need_id,
		reservation_id=reservation.id if reservation else None,
		donor_user_id=donor_user_id, donor_email=donor_email,
		is_test=(get_environment() == "test"),
	)

	application_fee_amount = round(amount_cents * platform_fee_percent / 100)
	try:
		session = create_donation_checkout_session(
			account.stripe_account_id, amount_cents, currency,
			PRODUCT_NAME_BY_TARGET.get(target_type, "Donation"), application_fee_amount,
			_append_redirect_params(success_url, donation.id), donation.id, customer_email=donor_email,
		)
	except Exception:
		# never leave an orphaned reservation holding up the pet's
		# allowance if Stripe itself rejects the checkout
		if reservation:
			limits_domain.release_reservation(reservation.id)
		donations_data.mark_failed(donation.id)
		raise

	donation = donations_data.set_checkout_session_id(donation.id, session.id)
	return {"donation": donation.to_dict(), "checkout_url": session.url}
