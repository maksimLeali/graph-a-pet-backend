"""HTTP routes for the Stripe Connect sample: seller onboarding/dashboard
(private, `/stripe-connect/...`) and the public storefront (`/store/...`).

Two Blueprints so `url_for('stripe_connect.xxx', ...)` /
`url_for('storefront.xxx', ...)` read clearly in stripe_connect/templates.py.
"""
from flask import Blueprint, request, redirect, url_for, render_template_string

from stripe_connect import StripeConfigError, get_sample_platform_price_id
from stripe_connect import data as stripe_data
from stripe_connect import service as stripe_service
from stripe_connect.templates import (
	TEST_MODE_BANNER,
	ERROR_PAGE,
	INDEX_PAGE,
	SELLER_DASHBOARD_PAGE,
	STOREFRONT_PAGE,
	SUCCESS_PAGE,
)
from utils.logger import logger

stripe_connect_bp = Blueprint("stripe_connect", __name__, url_prefix="/stripe-connect")
storefront_bp = Blueprint("storefront", __name__, url_prefix="/store")


def _error_page(title, message, back_url):
	return render_template_string(
		ERROR_PAGE, title=title, message=message, back_url=back_url,
		test_badge=TEST_MODE_BANNER,
	), 400


def _product_to_view(product):
	price = getattr(product, "default_price", None)
	price_label = None
	price_id = None
	if price and not isinstance(price, str):
		# `default_price` is only a full Price object when expanded (see
		# stripe_connect/service.list_products `expand=["data.default_price"]`)
		price_id = price.id
		if price.unit_amount is not None:
			price_label = f"{price.unit_amount / 100:.2f} {price.currency.upper()}"
	return {
		"id": product.id,
		"name": product.name,
		"description": getattr(product, "description", None),
		"price": price_label,
		"price_label": price_label,
		"price_id": price_id,
	}


# ---------------------------------------------------------------------------
# Seller onboarding + dashboard
# ---------------------------------------------------------------------------

@stripe_connect_bp.route("/", methods=["GET"])
def index():
	sellers = [s.to_dict() for s in stripe_data.list_connected_accounts()]
	return render_template_string(
		INDEX_PAGE,
		sellers=sellers,
		create_seller_url=url_for("stripe_connect.create_seller"),
		test_badge=TEST_MODE_BANNER,
	)


@stripe_connect_bp.route("/sellers", methods=["POST"])
def create_seller():
	display_name = request.form.get("display_name", "").strip()
	contact_email = request.form.get("contact_email", "").strip()
	if not display_name or not contact_email:
		return _error_page(
			"Missing fields", "Display name and contact email are required.",
			url_for("stripe_connect.index"),
		)

	try:
		account = stripe_service.create_connected_account(display_name, contact_email)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.index"))
	except Exception as e:
		logger.error(f"failed to create connected account: {e}")
		return _error_page("Could not create connected account", str(e), url_for("stripe_connect.index"))

	seller = stripe_data.create_connected_account_record(
		display_name=display_name, contact_email=contact_email, stripe_account_id=account.id,
	)
	return redirect(url_for("stripe_connect.seller_dashboard", seller_id=seller.id))


@stripe_connect_bp.route("/sellers/<seller_id>", methods=["GET"])
def seller_dashboard(seller_id):
	seller = stripe_data.get_connected_account(seller_id)
	if not seller:
		return _error_page("Not found", "No such seller.", url_for("stripe_connect.index"))

	try:
		status = stripe_service.get_account_status(seller.stripe_account_id)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.index"))
	except Exception as e:
		logger.error(f"failed to fetch account status for {seller.stripe_account_id}: {e}")
		return _error_page("Could not load account status", str(e), url_for("stripe_connect.index"))

	try:
		products = [_product_to_view(p) for p in stripe_service.list_products(seller.stripe_account_id)]
	except Exception as e:
		logger.error(f"failed to list products for {seller.stripe_account_id}: {e}")
		products = []

	subscription = stripe_data.get_subscription_for_account(seller.stripe_account_id)

	return render_template_string(
		SELLER_DASHBOARD_PAGE,
		seller=seller.to_dict(),
		status=status,
		products=products,
		subscription=subscription.to_dict() if subscription else None,
		test_badge=TEST_MODE_BANNER,
	)


@stripe_connect_bp.route("/sellers/<seller_id>/onboard/start", methods=["GET"])
def start_onboarding(seller_id):
	seller = stripe_data.get_connected_account(seller_id)
	if not seller:
		return _error_page("Not found", "No such seller.", url_for("stripe_connect.index"))

	refresh_url = url_for("stripe_connect.onboarding_refresh", seller_id=seller_id, _external=True)
	return_url = url_for("stripe_connect.onboarding_return", seller_id=seller_id, _external=True)

	try:
		link = stripe_service.create_onboarding_account_link(
			seller.stripe_account_id, refresh_url, return_url,
		)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))
	except Exception as e:
		logger.error(f"failed to create account link for {seller.stripe_account_id}: {e}")
		return _error_page("Could not start onboarding", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))

	return redirect(link.url)


@stripe_connect_bp.route("/sellers/<seller_id>/onboard/refresh", methods=["GET"])
def onboarding_refresh(seller_id):
	# The account link expired or was abandoned — this endpoint's only job
	# is to start a brand new one (Stripe calls it directly, no query args).
	return redirect(url_for("stripe_connect.start_onboarding", seller_id=seller_id))


@stripe_connect_bp.route("/sellers/<seller_id>/onboard/return", methods=["GET"])
def onboarding_return(seller_id):
	# Onboarding step finished (doesn't guarantee it's *complete* — the
	# dashboard re-checks live via get_account_status on every load).
	return redirect(url_for("stripe_connect.seller_dashboard", seller_id=seller_id))


@stripe_connect_bp.route("/sellers/<seller_id>/products", methods=["POST"])
def create_product(seller_id):
	seller = stripe_data.get_connected_account(seller_id)
	if not seller:
		return _error_page("Not found", "No such seller.", url_for("stripe_connect.index"))

	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	try:
		price_dollars = int(request.form.get("price", "0"))
	except ValueError:
		price_dollars = 0

	if not name or price_dollars <= 0:
		return _error_page(
			"Missing fields", "Name and a price greater than 0 are required.",
			url_for("stripe_connect.seller_dashboard", seller_id=seller_id),
		)

	try:
		stripe_service.create_product(
			seller.stripe_account_id, name, description, price_dollars * 100,
		)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))
	except Exception as e:
		logger.error(f"failed to create product for {seller.stripe_account_id}: {e}")
		return _error_page("Could not create product", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))

	return redirect(url_for("stripe_connect.seller_dashboard", seller_id=seller_id))


@stripe_connect_bp.route("/sellers/<seller_id>/subscribe", methods=["GET"])
def subscribe(seller_id):
	seller = stripe_data.get_connected_account(seller_id)
	if not seller:
		return _error_page("Not found", "No such seller.", url_for("stripe_connect.index"))

	success_url = (
		url_for("stripe_connect.seller_dashboard", seller_id=seller_id, _external=True)
		+ "?subscribed=1&session_id={CHECKOUT_SESSION_ID}"
	)
	cancel_url = url_for("stripe_connect.seller_dashboard", seller_id=seller_id, _external=True)

	try:
		price_id = get_sample_platform_price_id()
		session = stripe_service.create_platform_subscription_checkout_session(
			seller.stripe_account_id, price_id, success_url, cancel_url,
		)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))
	except Exception as e:
		logger.error(f"failed to create subscription checkout for {seller.stripe_account_id}: {e}")
		return _error_page("Could not start subscription checkout", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))

	return redirect(session.url)


@stripe_connect_bp.route("/sellers/<seller_id>/billing-portal", methods=["GET"])
def billing_portal(seller_id):
	seller = stripe_data.get_connected_account(seller_id)
	if not seller:
		return _error_page("Not found", "No such seller.", url_for("stripe_connect.index"))

	return_url = url_for("stripe_connect.seller_dashboard", seller_id=seller_id, _external=True)

	try:
		session = stripe_service.create_billing_portal_session(seller.stripe_account_id, return_url)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))
	except Exception as e:
		logger.error(f"failed to create billing portal session for {seller.stripe_account_id}: {e}")
		return _error_page("Could not open billing portal", str(e), url_for("stripe_connect.seller_dashboard", seller_id=seller_id))

	return redirect(session.url)


# ---------------------------------------------------------------------------
# Public storefront
# ---------------------------------------------------------------------------

@storefront_bp.route("/<stripe_account_id>", methods=["GET"])
def view_storefront(stripe_account_id):
	# Demo-only: keying the public storefront URL by the raw Stripe account
	# id (acct_...). A real integration should use an opaque store slug/
	# internal id instead and look up the Stripe account id server-side —
	# never expose acct_ ids to end customers.
	try:
		products = [_product_to_view(p) for p in stripe_service.list_products(stripe_account_id)]
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), "/")
	except Exception as e:
		logger.error(f"failed to list products for storefront {stripe_account_id}: {e}")
		return _error_page("Could not load storefront", str(e), "/")

	return render_template_string(
		STOREFRONT_PAGE,
		stripe_account_id=stripe_account_id,
		products=products,
		test_badge=TEST_MODE_BANNER,
	)


@storefront_bp.route("/<stripe_account_id>/checkout", methods=["POST"])
def checkout(stripe_account_id):
	price_id = request.form.get("price_id")
	if not price_id:
		return _error_page(
			"Missing price", "No price_id given.",
			url_for("storefront.view_storefront", stripe_account_id=stripe_account_id),
		)

	success_url = (
		url_for("storefront.success", stripe_account_id=stripe_account_id, _external=True)
		+ "?session_id={CHECKOUT_SESSION_ID}"
	)

	# PLACEHOLDER: flat 5% application fee for this demo — a real
	# integration would compute this from the actual line item amount(s).
	# Hardcoding it here means it's wrong for anything but a single
	# quantity-1 line item; fine for a sample, not for production.
	application_fee_amount = 0
	try:
		client = stripe_service.get_stripe_client()
		price = client.v1.prices.retrieve(price_id, {"stripe_account": stripe_account_id})
		if price.unit_amount:
			application_fee_amount = round(price.unit_amount * 0.05)
	except Exception as e:
		logger.error(f"failed to look up price {price_id} for fee calculation: {e}")

	try:
		session = stripe_service.create_direct_charge_checkout_session(
			stripe_account_id, price_id, success_url, application_fee_amount,
		)
	except StripeConfigError as e:
		return _error_page("Stripe is not configured", str(e), url_for("storefront.view_storefront", stripe_account_id=stripe_account_id))
	except Exception as e:
		logger.error(f"failed to create checkout session for {stripe_account_id}: {e}")
		return _error_page("Could not start checkout", str(e), url_for("storefront.view_storefront", stripe_account_id=stripe_account_id))

	return redirect(session.url)


@storefront_bp.route("/<stripe_account_id>/success", methods=["GET"])
def success(stripe_account_id):
	session_id = request.args.get("session_id", "")
	return render_template_string(
		SUCCESS_PAGE, session_id=session_id, test_badge=TEST_MODE_BANNER,
	)
