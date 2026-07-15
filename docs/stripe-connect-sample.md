# Stripe Connect sample integration

Self-contained demo, isolated from the GraphQL API (`stripe_connect/` package).
Onboards connected accounts, sells products through a storefront, and
subscribes a connected account to a platform plan. Test mode only.

## Setup

1. `pip install -r requirements.txt` (adds `stripe==15.3.0`)
2. `alembic upgrade head` (adds `stripe_connected_accounts` + `stripe_subscriptions`)
3. Fill in `config.yml` → `stripe:` section (all placeholders, see comments there):
   - `secret_key` — `sk_test_...`
   - `webhook_secret` — regular (non-thin) webhook signing secret, for subscription events
   - `thin_webhook_secret` — thin-events webhook signing secret, for V2 account requirement/capability events
   - `sample_platform_price_id` — a `price_...` for the subscription demo (only needed for the "Subscribe" button)

Leaving any of these as the placeholder value produces a clear error page
("Stripe is not configured: config.yml is missing a real value for
stripe.X"), never a raw 500 or a Stripe 401.

## Files added

| File | Purpose |
|---|---|
| `stripe_connect/__init__.py` | `get_stripe_client()` (single `StripeClient`, no top-level `type`), config placeholder detection |
| `stripe_connect/models.py` | `StripeConnectedAccount` (seller → `acct_...` mapping), `StripeSubscription` (status cache) |
| `stripe_connect/data.py` | DB query/insert helpers for the two models |
| `stripe_connect/service.py` | Stripe API wrappers — account create/retrieve (V2), account links (V2), products (`stripe_account` header), direct-charge checkout + application fee, subscription checkout (`customer_account`), billing portal |
| `stripe_connect/webhooks.py` | `/stripe-connect/webhooks/thin` (parses thin events, dispatches on `notification.type`) + `/stripe-connect/webhooks/subscriptions` (regular signed events, writes subscription status to DB) |
| `stripe_connect/routes.py` | Seller dashboard + public storefront routes |
| `stripe_connect/templates.py` | Inline Jinja2 HTML/CSS, `TEST MODE` badge on every page |
| `alembic/versions/c5d6e7f8a9b0_stripe_connect_sample.py` | Creates the two tables above |

## Files changed

- `requirements.txt` — `+stripe==15.3.0`, bumped `typing_extensions` (stripe's dependency)
- `config.yml` / `config_fields.yml` — `+stripe:` section (4 placeholders)
- `app.py` — registers the 3 new blueprints (`stripe_connect_bp`, `storefront_bp`, `stripe_webhooks`)

## Routes

```
GET  /stripe-connect/                              list/create sellers
POST /stripe-connect/sellers                       create connected account (V2)
GET  /stripe-connect/sellers/<id>                  dashboard — status always fetched live, never cached
GET  /stripe-connect/sellers/<id>/onboard/start     -> Stripe-hosted onboarding (Account Link)
GET  /stripe-connect/sellers/<id>/onboard/refresh   refresh_url target
GET  /stripe-connect/sellers/<id>/onboard/return    return_url target
POST /stripe-connect/sellers/<id>/products          create product on the connected account
GET  /stripe-connect/sellers/<id>/subscribe         -> Checkout (subscription, customer_account)
GET  /stripe-connect/sellers/<id>/billing-portal    -> Stripe billing portal

GET  /store/<acct_id>                               public storefront (uses raw acct_ id — comment: use an opaque id in production)
POST /store/<acct_id>/checkout                      direct charge + 5% application fee -> Checkout
GET  /store/<acct_id>/success                       success page

POST /stripe-connect/webhooks/thin                  V2 account requirement/capability updates
POST /stripe-connect/webhooks/subscriptions          customer.subscription.*, payment_method.*, customer.*, tax_id.*, billing_portal.*
```

## Webhook Dashboard setup

Full step-by-step (event selection, thin vs regular payload style, local
`stripe listen` commands) is in the module docstring at the top of
`stripe_connect/webhooks.py`.

## Known gaps / not done

- Not tested against a real Stripe key (no key available in this environment) — only verified: page rendering, DB writes, placeholder-config error paths, and webhook signature-rejection (all via a locally-run server + curl).
- Application fee is a flat 5%, single line-item assumption — fine for a demo, not for production.
- `payment_method.*` / `customer.updated` / `customer.tax_id.*` webhook handlers only log + `TODO` (no dedicated table was asked for beyond subscription status).
