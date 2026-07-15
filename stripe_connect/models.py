"""DB models for the Stripe Connect sample.

**RETIRED as of migration `e7f8a9b0c1d2_donations_core`**: the
`stripe_connected_accounts` / `stripe_subscriptions` tables these classes
map to were dropped and replaced by the real, shelter-scoped
`repository/donations/models.py::StripeConnectedAccount` (donation
subscriptions were dropped from scope entirely). Importing this module
against the current schema will fail at query time (table doesn't exist).
It is kept only for reference — see docs/stripe-connect-sample.md — and is
never imported by app.py by default (`stripe_connect.SAMPLE_ENABLED`).

Uses the same `db`/`Base` as every other repository module in this app
(shared metadata/engine, `id`/`created_at`/`updated_at` from `Base`).

NOTE on design: this sample treats "the seller signing up for Connect" as
its own tiny table (`StripeConnectedAccount`) rather than bolting a
`stripe_account_id` column onto the real `users` table, since Graph-a-Pet's
Users are pet owners/shelter staff, not marketplace sellers. In a real
integration you would instead add a nullable `stripe_account_id` column
directly to whichever of your own tables represents "the seller" (e.g.
Shelter, if shelters became Connect payees) and skip this table entirely.
"""
from repository import db, Base


class StripeConnectedAccount(Base):
	__tablename__ = "stripe_connected_accounts"

	# Stand-in "user" for this demo — see module docstring.
	display_name = db.Column(db.String, nullable=False)
	contact_email = db.Column(db.String, nullable=False)

	# acct_... — the mapping the task asks us to store ("store a mapping
	# from the user object to the account ID"). Everything else about the
	# account (onboarding/verification/capability status) is fetched live
	# from the Accounts API on every page load, never cached here — see
	# stripe_connect/service.get_account_status.
	stripe_account_id = db.Column(db.String, nullable=False, unique=True, index=True)

	def to_dict(self):
		return {
			"id": self.id,
			"display_name": self.display_name,
			"contact_email": self.contact_email,
			"stripe_account_id": self.stripe_account_id,
			"created_at": str(self.created_at),
		}


class StripeSubscription(Base):
	__tablename__ = "stripe_subscriptions"

	stripe_subscription_id = db.Column(db.String, nullable=False, unique=True, index=True)

	# V2 connected accounts ARE their own customer: a subscription's
	# `customer_account` field is the connected account id (acct_...).
	# Never read `.customer` for a V2-account subscription — see the
	# "General Tips" note in stripe_connect/webhooks.py.
	stripe_account_id = db.Column(db.String, nullable=False, index=True)

	price_id = db.Column(db.String, nullable=True)
	status = db.Column(db.String, nullable=False, default="incomplete")
	cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)

	def to_dict(self):
		return {
			"id": self.id,
			"stripe_subscription_id": self.stripe_subscription_id,
			"stripe_account_id": self.stripe_account_id,
			"price_id": self.price_id,
			"status": self.status,
			"cancel_at_period_end": self.cancel_at_period_end,
			"created_at": str(self.created_at),
			"updated_at": str(self.updated_at) if self.updated_at else None,
		}
