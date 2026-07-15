"""Shared Stripe infrastructure: client init + config validation + test-mode
guards, used by BOTH:

  * `domain/donations/` + `api/donations/` — the real, production
    Graph-a-Pet donation feature (repository -> domain -> api, GraphQL-only
    frontend access). This is the actual integration.
  * `stripe_connect/routes.py` + `webhooks.py` — the original proof-of-concept
    (seller onboarding demo, product storefront, platform subscriptions).
    Kept only as an isolated, clearly-flagged dev sample — see
    `stripe_connect.SAMPLE_ENABLED` and its registration guard in `app.py`.
    None of its product/storefront/subscription code is reused by the real
    donation domain (see docs/stripe-connect-sample.md for what stayed
    sample-only vs what moved into the real integration).

Everything below (client factory, config placeholder validation, live-key
rejection) IS reused by the real donation domain — this module is the
common foundation, not sample-only code.
"""
import stripe
from config import cfg

# Sentinel placeholder values written into config.yml / config_fields.yml.
# Comparing against these (rather than just checking truthiness) means a
# copy-pasted-but-unedited config still produces a clear error instead of a
# confusing 401 from Stripe.
_PLACEHOLDERS = {
	"secret_key": "sk_test_REPLACE_ME",
	"webhook_secret": "whsec_REPLACE_ME",
	"thin_webhook_secret": "whsec_REPLACE_ME",
	"sample_platform_price_id": "price_REPLACE_ME",
}

# Whether the original proof-of-concept routes (seller dashboard, product
# storefront, platform subscriptions) get registered in app.py at all. Off
# by default — flip on locally for manual testing of the sample only.
# Never enable in a deployed environment: it has no bearing on the real
# donation feature and only exists for reference/comparison.
SAMPLE_ENABLED = bool((cfg.get("stripe") or {}).get("enable_legacy_sample", False))


class StripeConfigError(RuntimeError):
	"""Raised when a required stripe.* config value is missing or still the
	placeholder from config.yml. Message tells the developer exactly which
	key to fill in and where."""
	pass


class StripeTestModeError(RuntimeError):
	"""Raised when a live-mode secret key, or a livemode=true Stripe object
	or event, is encountered while the app is running in test mode. The
	whole donation feature is test-only for now — see the task's "Test
	mode" requirements — so this is a hard stop, not a warning."""
	pass


def _get_config_value(key: str) -> str:
	value = (cfg.get("stripe") or {}).get(key)
	if not value or value == _PLACEHOLDERS.get(key):
		raise StripeConfigError(
			f"config.yml is missing a real value for stripe.{key}. "
			f"Replace the placeholder '{_PLACEHOLDERS.get(key)}' with a real "
			f"value (see the comment above stripe.{key} in config.yml)."
		)
	return value


def get_stripe_secret_key() -> str:
	key = _get_config_value("secret_key")
	if key.startswith("sk_live_"):
		# The whole feature is test-only right now (see "Test mode" in the
		# task spec) — refuse to even construct a client with a live key
		# rather than rely on every call site remembering to check.
		raise StripeTestModeError(
			"stripe.secret_key is a live-mode key (sk_live_...). The donation "
			"feature only supports test mode right now — use an sk_test_ key."
		)
	return key


def get_webhook_secret() -> str:
	"""Signing secret for the regular (non-thin) webhook endpoint — used for
	subscription lifecycle events. See stripe_connect/webhooks.py."""
	return _get_config_value("webhook_secret")


def get_thin_webhook_secret() -> str:
	"""Signing secret for the thin-events endpoint — used for V2 connected
	account requirement/capability updates. See stripe_connect/webhooks.py."""
	return _get_config_value("thin_webhook_secret")


def get_sample_platform_price_id() -> str:
	"""Placeholder platform-level recurring Price ID that connected accounts
	subscribe to in the subscription demo. This one intentionally does NOT
	need to be real for the rest of the module to work — only the
	"Subscribe" button needs it, and it fails with a clear error rather than
	a raw Stripe 400 if it's still the placeholder. Sample-only — the real
	donation domain has no subscription concept."""
	return _get_config_value("sample_platform_price_id")


def get_platform_fee_percent() -> float:
	"""Percentage (0-100) of the gross donation amount kept as the platform
	fee. Never hardcoded at a call site — every donation stores the
	percentage that was actually applied (see Donation.platform_fee_percent)
	so a later config change doesn't retroactively change historical
	donations' displayed fee."""
	value = (cfg.get("stripe") or {}).get("platform_fee_percent")
	return float(value) if value is not None else 10.0


def get_default_pet_monthly_limit_cents() -> int:
	"""Default monthly donation allowance for a pet with no
	PetDonationPolicy override, in integer minor currency units (cents)."""
	value = (cfg.get("stripe") or {}).get("default_pet_monthly_limit_cents")
	return int(value) if value is not None else 5000


def get_environment() -> str:
	"""'test' or 'live' — drives the TEST MODE badges/metadata and the
	livemode=true rejection in webhook processing. Independent from which
	Stripe key is configured (both are checked): this is the application's
	own declared environment, `get_stripe_secret_key` checks the key
	itself."""
	return (cfg.get("stripe") or {}).get("environment") or "test"


def get_stripe_client() -> stripe.StripeClient:
	"""The one `StripeClient` used for every Stripe request in this app —
	both the real donation domain and the legacy sample. Never construct ad
	hoc `stripe.Product.create(...)`-style top-level calls. The Stripe API
	version is intentionally not set here — the installed SDK version
	(stripe==15.3.0, see requirements.txt) pins its own default/pinned API
	version automatically.
	"""
	return stripe.StripeClient(get_stripe_secret_key())
