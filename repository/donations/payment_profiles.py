import uuid
from datetime import datetime

from repository import db
from repository.donations.models import UserPaymentProfile, UserPaymentMethod, PaymentMethodConsent


def _new_id():
	return f"{uuid.uuid4()}"


def get_profile_for_user(user_id):
	return db.session.query(UserPaymentProfile).filter(UserPaymentProfile.user_id == user_id).first()


def create_profile(user_id, stripe_customer_id):
	model = UserPaymentProfile(
		id=_new_id(), user_id=user_id, stripe_customer_id=stripe_customer_id,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def set_default_payment_method(profile_id, user_payment_method_id):
	model = db.session.query(UserPaymentProfile).filter(UserPaymentProfile.id == profile_id).first()
	if model is None:
		return None
	model.default_payment_method_id = user_payment_method_id
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def list_payment_methods(profile_id, active_only=True):
	q = db.session.query(UserPaymentMethod).filter(UserPaymentMethod.user_payment_profile_id == profile_id)
	if active_only:
		q = q.filter(UserPaymentMethod.is_active.is_(True))
	return q.order_by(UserPaymentMethod.created_at.desc()).all()


def get_payment_method(payment_method_id):
	return db.session.query(UserPaymentMethod).filter(UserPaymentMethod.id == payment_method_id).first()


def create_payment_method(profile_id, stripe_payment_method_id, card_brand=None, card_last4=None,
						   card_exp_month=None, card_exp_year=None):
	model = UserPaymentMethod(
		id=_new_id(),
		user_payment_profile_id=profile_id,
		stripe_payment_method_id=stripe_payment_method_id,
		card_brand=card_brand,
		card_last4=card_last4,
		card_exp_month=card_exp_month,
		card_exp_year=card_exp_year,
		is_active=True,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	db.session.commit()
	return model


def deactivate_payment_method(payment_method_id):
	model = get_payment_method(payment_method_id)
	if model is None:
		return None
	model.is_active = False
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def record_consent(user_payment_method_id, consent_text, ip_address=None):
	"""Immutable — never updated/deleted after insert."""
	model = PaymentMethodConsent(
		id=_new_id(),
		user_payment_method_id=user_payment_method_id,
		consented_at=datetime.utcnow(),
		consent_text=consent_text,
		ip_address=ip_address,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	db.session.commit()
	return model
