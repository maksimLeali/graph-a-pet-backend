"""Graph-a-Pet donation domain — repository models.

All monetary values are integer minor currency units (cents) — never
floats. `FinancialMovement` and `StripeWebhookEvent` are treated as
append-only: application code must never UPDATE or DELETE a row in either
table once inserted (corrections are new compensating rows) — see
domain/donations/ledger.py and domain/donations/webhooks.py.

Note on the two circular relationships (Donation <-> DonationLimitReservation,
UserPaymentProfile <-> UserPaymentMethod): rather than a two-step
create-table-then-ALTER-ADD-CONSTRAINT dance, only one direction of each
pair is a real FK (enforced by Postgres); the other is a plain indexed
String column populated by application code. See the migration for which
direction was chosen and why.
"""
import enum
from sqlalchemy.dialects.postgresql import JSONB
from repository import db, Base

# ensure FK targets are registered in the shared metadata even when this
# package is imported standalone (mirrors repository/authorization/__init__.py)
import repository.shelters.models  # noqa: F401
import repository.pets.models  # noqa: F401
import repository.users.models  # noqa: F401
from utils.dates import iso_z


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConnectedAccountEnvironment(enum.Enum):
	TEST = "TEST"
	LIVE = "LIVE"


class DonationTargetType(enum.Enum):
	SHELTER = "SHELTER"
	PET = "PET"
	PET_FUNDING_NEED = "PET_FUNDING_NEED"


class DonorType(enum.Enum):
	GUEST = "GUEST"
	AUTHENTICATED = "AUTHENTICATED"


class DonationStatus(enum.Enum):
	PENDING = "PENDING"
	PROCESSING = "PROCESSING"
	SUCCEEDED = "SUCCEEDED"
	FAILED = "FAILED"
	CANCELED = "CANCELED"


class RefundStatus(enum.Enum):
	NONE = "NONE"
	PARTIAL = "PARTIAL"
	FULL = "FULL"


class DisputeStatus(enum.Enum):
	NONE = "NONE"
	OPEN = "OPEN"
	WON = "WON"
	LOST = "LOST"


class MovementType(enum.Enum):
	GROSS_PAYMENT = "GROSS_PAYMENT"
	PLATFORM_FEE = "PLATFORM_FEE"
	PROCESSING_FEE = "PROCESSING_FEE"
	SHELTER_NET = "SHELTER_NET"
	# Direct Charges (what this integration uses) settle straight onto the
	# connected account's own Stripe balance — there is no separate
	# Transfer object like a Destination Charge would produce. TRANSFER is
	# kept for schema completeness (task's ledger movement list) and for a
	# future Destination-Charge model; PAYOUT is real and used today, from
	# payout.* webhook events (see domain/donations/webhooks.py).
	TRANSFER = "TRANSFER"
	PAYOUT = "PAYOUT"
	REFUND = "REFUND"
	DISPUTE = "DISPUTE"
	REVERSAL = "REVERSAL"
	ADJUSTMENT = "ADJUSTMENT"


class FundingNeedStatus(enum.Enum):
	ACTIVE = "ACTIVE"
	CLOSED = "CLOSED"


class ExpenseStatus(enum.Enum):
	DRAFT = "DRAFT"
	SUBMITTED = "SUBMITTED"
	APPROVED = "APPROVED"
	REJECTED = "REJECTED"


class ReservationStatus(enum.Enum):
	ACTIVE = "ACTIVE"
	CONSUMED = "CONSUMED"
	RELEASED = "RELEASED"
	EXPIRED = "EXPIRED"


class WebhookEventStatus(enum.Enum):
	RECEIVED = "RECEIVED"
	PROCESSED = "PROCESSED"
	FAILED = "FAILED"
	IGNORED = "IGNORED"


# ---------------------------------------------------------------------------
# Connected accounts (shelter-scoped — replaces the sample's generic seller)
# ---------------------------------------------------------------------------

class StripeConnectedAccount(Base):
	__tablename__ = "stripe_connected_accounts"
	__table_args__ = (
		# a shelter may have only one ACTIVE connected account per
		# environment (re-onboarding after disconnecting inserts a new row
		# and leaves the old one is_active=False rather than mutating it)
		db.Index(
			"ux_stripe_connected_accounts_shelter_env_active",
			"shelter_id", "environment",
			unique=True,
			postgresql_where=db.text("is_active"),
		),
		Base.__table_args__,
	)

	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	stripe_account_id = db.Column(db.String, nullable=False, unique=True, index=True)
	environment = db.Column(db.Enum(ConnectedAccountEnvironment), nullable=False,
							 default=ConnectedAccountEnvironment.TEST)

	# denormalized cache of the last `get_account_status` read — a real
	# integration re-syncs these via account.updated webhooks + the manual
	# "refresh" mutation, but never invents a status without an API/webhook
	# read backing it
	onboarding_status = db.Column(db.String, nullable=False, default="not_started")
	verification_status = db.Column(db.String, nullable=False, default="unverified")
	charges_enabled = db.Column(db.Boolean, nullable=False, default=False)
	payouts_enabled = db.Column(db.Boolean, nullable=False, default=False)
	details_submitted = db.Column(db.Boolean, nullable=False, default=False)

	donations_enabled = db.Column(db.Boolean, nullable=False, default=False)
	# null = shelter uses the global platform default (stripe config); see
	# domain/donations/limits.get_effective_limit_cents for the fallback chain
	default_pet_monthly_limit_cents = db.Column(db.Integer, nullable=True)
	is_active = db.Column(db.Boolean, nullable=False, default=True)
	last_synced_at = db.Column(db.DateTime, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"shelter_id": self.shelter_id,
			"stripe_account_id": self.stripe_account_id,
			"environment": self.environment.name if self.environment else None,
			"onboarding_status": self.onboarding_status,
			"verification_status": self.verification_status,
			"charges_enabled": bool(self.charges_enabled),
			"payouts_enabled": bool(self.payouts_enabled),
			"details_submitted": bool(self.details_submitted),
			"donations_enabled": bool(self.donations_enabled),
			"default_pet_monthly_limit_cents": self.default_pet_monthly_limit_cents,
			"is_active": bool(self.is_active),
			"last_synced_at": iso_z(self.last_synced_at) if self.last_synced_at else None,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


# ---------------------------------------------------------------------------
# Pet funding needs
# ---------------------------------------------------------------------------

class PetFundingNeed(Base):
	__tablename__ = "pet_funding_needs"

	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	# nullable: a funding need can be shelter-general or pet-specific
	pet_id = db.Column(db.String, db.ForeignKey("pets.id"), nullable=True, index=True)

	title = db.Column(db.String, nullable=False)
	description = db.Column(db.Text, nullable=True)
	category = db.Column(db.String, nullable=True)

	currency = db.Column(db.String, nullable=False, default="usd")
	target_amount_cents = db.Column(db.Integer, nullable=False)
	# gross amount of every SUCCEEDED donation targeting this need — kept in
	# sync by domain/donations/webhooks.py on payment_intent.succeeded, never
	# recomputed from Stripe redirects
	collected_amount_cents = db.Column(db.Integer, nullable=False, default=0)

	status = db.Column(db.Enum(FundingNeedStatus), nullable=False, default=FundingNeedStatus.ACTIVE)
	starts_at = db.Column(db.DateTime, nullable=True)
	ends_at = db.Column(db.DateTime, nullable=True)
	closed_at = db.Column(db.DateTime, nullable=True)

	def to_dict(self):
		remaining = max(self.target_amount_cents - self.collected_amount_cents, 0)
		return {
			"id": self.id,
			"shelter_id": self.shelter_id,
			"pet_id": self.pet_id,
			"title": self.title,
			"description": self.description,
			"category": self.category,
			"currency": self.currency,
			"target_amount_cents": self.target_amount_cents,
			"collected_amount_cents": self.collected_amount_cents,
			"remaining_amount_cents": remaining,
			"status": self.status.name if self.status else None,
			"starts_at": iso_z(self.starts_at) if self.starts_at else None,
			"ends_at": iso_z(self.ends_at) if self.ends_at else None,
			"closed_at": iso_z(self.closed_at) if self.closed_at else None,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


# ---------------------------------------------------------------------------
# Pet donation limits
# ---------------------------------------------------------------------------

class PetDonationPolicy(Base):
	__tablename__ = "pet_donation_policies"
	__table_args__ = (
		db.UniqueConstraint("pet_id", name="uq_pet_donation_policies_pet"),
		Base.__table_args__,
	)

	pet_id = db.Column(db.String, db.ForeignKey("pets.id"), nullable=False, index=True)
	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	# permanent override of the global default (config
	# default_pet_monthly_limit_cents); null = use the default
	custom_monthly_limit_cents = db.Column(db.Integer, nullable=True)
	is_active = db.Column(db.Boolean, nullable=False, default=True)

	# Temporary override of the effective limit (permanent-if-set, else the
	# global default) for a bounded window. Only one active override per
	# pet — a new call to createTemporaryPetLimitOverride replaces these
	# fields; "limit history" is derived from DonationLimitReservation rows
	# (see repository/donations/limits.list_reservation_history_for_pet),
	# since the task's fixed 10-model list has no dedicated override-log
	# table — see docs/donations-backend.md for this design note.
	temporary_override_cents = db.Column(db.Integer, nullable=True)
	temporary_override_reason = db.Column(db.Text, nullable=True)
	temporary_override_effective_at = db.Column(db.DateTime, nullable=True)
	temporary_override_expires_at = db.Column(db.DateTime, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"pet_id": self.pet_id,
			"shelter_id": self.shelter_id,
			"custom_monthly_limit_cents": self.custom_monthly_limit_cents,
			"is_active": bool(self.is_active),
			"temporary_override_cents": self.temporary_override_cents,
			"temporary_override_reason": self.temporary_override_reason,
			"temporary_override_effective_at": iso_z(self.temporary_override_effective_at) if self.temporary_override_effective_at else None,
			"temporary_override_expires_at": iso_z(self.temporary_override_expires_at) if self.temporary_override_expires_at else None,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


class DonationLimitReservation(Base):
	"""Atomic hold against a pet's remaining monthly allowance, created
	BEFORE the Stripe Checkout Session so a payment can never be created
	past the limit — see domain/donations/limits.py `reserve_pet_allowance`
	(uses a Postgres advisory lock keyed by pet_id+period to make the
	reserve-then-insert step race-free under concurrent donations)."""
	__tablename__ = "donation_limit_reservations"

	pet_id = db.Column(db.String, db.ForeignKey("pets.id"), nullable=False, index=True)
	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	period_start = db.Column(db.DateTime, nullable=False)
	period_end = db.Column(db.DateTime, nullable=False)
	amount_cents = db.Column(db.Integer, nullable=False)
	status = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.ACTIVE)
	expires_at = db.Column(db.DateTime, nullable=False)
	override_reason = db.Column(db.Text, nullable=True)
	override_expires_at = db.Column(db.DateTime, nullable=True)
	# plain indexed column, not a DB FK — see module docstring. Set once the
	# reservation is attached to a real Donation row (which DOES have a
	# real FK back to this table via Donation.reservation_id).
	donation_id = db.Column(db.String, nullable=True, index=True)

	def to_dict(self):
		return {
			"id": self.id,
			"pet_id": self.pet_id,
			"shelter_id": self.shelter_id,
			"period_start": iso_z(self.period_start),
			"period_end": iso_z(self.period_end),
			"amount_cents": self.amount_cents,
			"status": self.status.name if self.status else None,
			"expires_at": iso_z(self.expires_at),
			"override_reason": self.override_reason,
			"override_expires_at": iso_z(self.override_expires_at) if self.override_expires_at else None,
			"donation_id": self.donation_id,
			"created_at": iso_z(self.created_at),
		}


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------

class Donation(Base):
	__tablename__ = "donations"

	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	connected_account_id = db.Column(db.String, db.ForeignKey("stripe_connected_accounts.id"), nullable=False)

	target_type = db.Column(db.Enum(DonationTargetType), nullable=False)
	pet_id = db.Column(db.String, db.ForeignKey("pets.id"), nullable=True, index=True)
	funding_need_id = db.Column(db.String, db.ForeignKey("pet_funding_needs.id"), nullable=True, index=True)
	# real FK — see module docstring on the circular-relationship choice
	reservation_id = db.Column(db.String, db.ForeignKey("donation_limit_reservations.id"), nullable=True)

	donor_type = db.Column(db.Enum(DonorType), nullable=False)
	donor_user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
	donor_email = db.Column(db.String, nullable=True)

	currency = db.Column(db.String, nullable=False, default="usd")
	gross_amount_cents = db.Column(db.Integer, nullable=False)
	# stored on every donation so a later config change never retroactively
	# changes a historical donation's displayed fee/net split
	platform_fee_percent = db.Column(db.Float, nullable=False)
	platform_fee_amount_cents = db.Column(db.Integer, nullable=False, default=0)
	# only known once Stripe reports the balance transaction (webhook) —
	# null until then, never estimated
	processing_fee_amount_cents = db.Column(db.Integer, nullable=True)
	shelter_net_amount_cents = db.Column(db.Integer, nullable=True)

	status = db.Column(db.Enum(DonationStatus), nullable=False, default=DonationStatus.PENDING)
	refund_status = db.Column(db.Enum(RefundStatus), nullable=False, default=RefundStatus.NONE)
	refunded_amount_cents = db.Column(db.Integer, nullable=False, default=0)
	dispute_status = db.Column(db.Enum(DisputeStatus), nullable=False, default=DisputeStatus.NONE)

	is_test = db.Column(db.Boolean, nullable=False, default=True)

	stripe_checkout_session_id = db.Column(db.String, nullable=True, index=True)
	stripe_payment_intent_id = db.Column(db.String, nullable=True, unique=True, index=True)

	def to_dict(self):
		return {
			"id": self.id,
			"shelter_id": self.shelter_id,
			"connected_account_id": self.connected_account_id,
			"target_type": self.target_type.name if self.target_type else None,
			"pet_id": self.pet_id,
			"funding_need_id": self.funding_need_id,
			"reservation_id": self.reservation_id,
			"donor_type": self.donor_type.name if self.donor_type else None,
			"donor_user_id": self.donor_user_id,
			"donor_email": self.donor_email,
			"currency": self.currency,
			"gross_amount_cents": self.gross_amount_cents,
			"platform_fee_percent": self.platform_fee_percent,
			"platform_fee_amount_cents": self.platform_fee_amount_cents,
			"processing_fee_amount_cents": self.processing_fee_amount_cents,
			"shelter_net_amount_cents": self.shelter_net_amount_cents,
			"status": self.status.name if self.status else None,
			"refund_status": self.refund_status.name if self.refund_status else None,
			"refunded_amount_cents": self.refunded_amount_cents,
			"dispute_status": self.dispute_status.name if self.dispute_status else None,
			"is_test": bool(self.is_test),
			"stripe_checkout_session_id": self.stripe_checkout_session_id,
			"stripe_payment_intent_id": self.stripe_payment_intent_id,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


# ---------------------------------------------------------------------------
# Ledger — append-only, see module docstring
# ---------------------------------------------------------------------------

class FinancialMovement(Base):
	__tablename__ = "financial_movements"
	__table_args__ = (
		# replaying the same Stripe object for the same donation/movement
		# type is a no-op instead of a duplicate row (webhook redelivery)
		db.UniqueConstraint(
			"donation_id", "movement_type", "stripe_object_id",
			name="uq_financial_movements_donation_type_object",
		),
		Base.__table_args__,
	)

	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	donation_id = db.Column(db.String, db.ForeignKey("donations.id"), nullable=True, index=True)
	movement_type = db.Column(db.Enum(MovementType), nullable=False, index=True)
	# signed so every donation's movements sum to exactly zero (standard
	# double-entry balance — see repository/donations/ledger.is_balanced):
	# GROSS_PAYMENT +gross (received into the transaction), PLATFORM_FEE
	# and PROCESSING_FEE negative (leave the transaction), SHELTER_NET
	# negative (= -(gross - both fees), leaves the transaction into the
	# shelter's payable balance — display layers show `abs()` of this to
	# shelters/platform staff as "net amount"), REFUND/DISPUTE/REVERSAL
	# negative (money leaving), ADJUSTMENT either sign to balance a
	# correction
	amount_cents = db.Column(db.Integer, nullable=False)
	currency = db.Column(db.String, nullable=False, default="usd")
	stripe_object_id = db.Column(db.String, nullable=True, index=True)
	description = db.Column(db.Text, nullable=True)
	is_test = db.Column(db.Boolean, nullable=False, default=True)

	def to_dict(self):
		return {
			"id": self.id,
			"shelter_id": self.shelter_id,
			"donation_id": self.donation_id,
			"movement_type": self.movement_type.name if self.movement_type else None,
			"amount_cents": self.amount_cents,
			"currency": self.currency,
			"stripe_object_id": self.stripe_object_id,
			"description": self.description,
			"is_test": bool(self.is_test),
			"created_at": iso_z(self.created_at),
		}


# ---------------------------------------------------------------------------
# Shelter expenses
# ---------------------------------------------------------------------------

class ShelterExpense(Base):
	__tablename__ = "shelter_expenses"

	shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
	pet_id = db.Column(db.String, db.ForeignKey("pets.id"), nullable=True)
	funding_need_id = db.Column(db.String, db.ForeignKey("pet_funding_needs.id"), nullable=True)

	currency = db.Column(db.String, nullable=False, default="usd")
	amount_cents = db.Column(db.Integer, nullable=False)
	description = db.Column(db.Text, nullable=False)

	status = db.Column(db.Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.DRAFT)
	created_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
	submitted_at = db.Column(db.DateTime, nullable=True)
	approved_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
	approved_at = db.Column(db.DateTime, nullable=True)
	rejected_reason = db.Column(db.Text, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"shelter_id": self.shelter_id,
			"pet_id": self.pet_id,
			"funding_need_id": self.funding_need_id,
			"currency": self.currency,
			"amount_cents": self.amount_cents,
			"description": self.description,
			"status": self.status.name if self.status else None,
			"created_by_id": self.created_by_id,
			"submitted_at": iso_z(self.submitted_at) if self.submitted_at else None,
			"approved_by_id": self.approved_by_id,
			"approved_at": iso_z(self.approved_at) if self.approved_at else None,
			"rejected_reason": self.rejected_reason,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


# ---------------------------------------------------------------------------
# Stripe webhook events — append-only, see module docstring
# ---------------------------------------------------------------------------

class StripeWebhookEvent(Base):
	__tablename__ = "stripe_webhook_events"
	__table_args__ = (
		db.UniqueConstraint("stripe_event_id", name="uq_stripe_webhook_events_event_id"),
		Base.__table_args__,
	)

	stripe_event_id = db.Column(db.String, nullable=False, index=True)
	event_type = db.Column(db.String, nullable=False, index=True)
	livemode = db.Column(db.Boolean, nullable=False, default=False)
	status = db.Column(db.Enum(WebhookEventStatus), nullable=False, default=WebhookEventStatus.RECEIVED)
	attempts = db.Column(db.Integer, nullable=False, default=0)
	last_error = db.Column(db.Text, nullable=True)
	payload = db.Column(JSONB, nullable=True)
	processed_at = db.Column(db.DateTime, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"stripe_event_id": self.stripe_event_id,
			"event_type": self.event_type,
			"livemode": bool(self.livemode),
			"status": self.status.name if self.status else None,
			"attempts": self.attempts,
			"last_error": self.last_error,
			"processed_at": iso_z(self.processed_at) if self.processed_at else None,
			"created_at": iso_z(self.created_at),
		}


# ---------------------------------------------------------------------------
# Donor payment profiles (authenticated donors only — guests never get one)
# ---------------------------------------------------------------------------

class UserPaymentProfile(Base):
	__tablename__ = "user_payment_profiles"
	__table_args__ = (
		db.UniqueConstraint("user_id", name="uq_user_payment_profiles_user"),
		Base.__table_args__,
	)

	user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False, index=True)
	stripe_customer_id = db.Column(db.String, nullable=False, unique=True)
	# plain indexed column, not a DB FK — see module docstring
	default_payment_method_id = db.Column(db.String, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"user_id": self.user_id,
			"stripe_customer_id": self.stripe_customer_id,
			"default_payment_method_id": self.default_payment_method_id,
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


class UserPaymentMethod(Base):
	"""Never stores a full card number or CVC — Stripe itself never returns
	either; only the masked display fields below (brand/last4/exp) are
	persisted, mirrored from the PaymentMethod object."""
	__tablename__ = "user_payment_methods"
	__table_args__ = (
		db.UniqueConstraint("stripe_payment_method_id", name="uq_user_payment_methods_pm"),
		Base.__table_args__,
	)

	user_payment_profile_id = db.Column(db.String, db.ForeignKey("user_payment_profiles.id"),
										 nullable=False, index=True)
	stripe_payment_method_id = db.Column(db.String, nullable=False)
	card_brand = db.Column(db.String, nullable=True)
	card_last4 = db.Column(db.String, nullable=True)
	card_exp_month = db.Column(db.Integer, nullable=True)
	card_exp_year = db.Column(db.Integer, nullable=True)
	is_active = db.Column(db.Boolean, nullable=False, default=True)

	def to_dict(self):
		return {
			"id": self.id,
			"user_payment_profile_id": self.user_payment_profile_id,
			"stripe_payment_method_id": self.stripe_payment_method_id,
			"card_brand": self.card_brand,
			"card_last4": self.card_last4,
			"card_exp_month": self.card_exp_month,
			"card_exp_year": self.card_exp_year,
			"is_active": bool(self.is_active),
			"created_at": iso_z(self.created_at),
			"updated_at": iso_z(self.updated_at) if self.updated_at else None,
		}


class PaymentMethodConsent(Base):
	"""Immutable audit record of the explicit consent required before
	saving a payment method (never updated/deleted after insert)."""
	__tablename__ = "payment_method_consents"

	user_payment_method_id = db.Column(db.String, db.ForeignKey("user_payment_methods.id"),
										nullable=False, index=True)
	consented_at = db.Column(db.DateTime, nullable=False)
	consent_text = db.Column(db.Text, nullable=False)
	ip_address = db.Column(db.String, nullable=True)

	def to_dict(self):
		return {
			"id": self.id,
			"user_payment_method_id": self.user_payment_method_id,
			"consented_at": iso_z(self.consented_at),
			"consent_text": self.consent_text,
			"ip_address": self.ip_address,
			"created_at": iso_z(self.created_at),
		}
