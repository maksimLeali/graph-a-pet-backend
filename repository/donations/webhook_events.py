"""Append-only webhook event log. Persisting BEFORE processing (see
`create_received_event`) plus the DB unique constraint on `stripe_event_id`
is what makes duplicate/retried deliveries safe (domain/donations/webhooks.py
catches the IntegrityError and treats it as an already-seen event)."""
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from repository import db
from repository.donations.models import StripeWebhookEvent, WebhookEventStatus


def _new_id():
	return f"{uuid.uuid4()}"


def get_by_stripe_event_id(stripe_event_id):
	return db.session.query(StripeWebhookEvent).filter(
		StripeWebhookEvent.stripe_event_id == stripe_event_id
	).first()


def create_received_event(stripe_event_id, event_type, livemode, payload=None):
	"""Returns (model, created). created=False means this exact event id
	was already persisted — a duplicate delivery, not an error."""
	model = StripeWebhookEvent(
		id=_new_id(),
		stripe_event_id=stripe_event_id,
		event_type=event_type,
		livemode=livemode,
		status=WebhookEventStatus.RECEIVED,
		attempts=1,
		payload=payload,
		created_at=datetime.utcnow(),
	)
	db.session.add(model)
	try:
		db.session.commit()
		return model, True
	except IntegrityError:
		db.session.rollback()
		existing = get_by_stripe_event_id(stripe_event_id)
		if existing:
			existing.attempts = (existing.attempts or 0) + 1
			db.session.commit()
		return existing, False


def mark_processed(event_id):
	model = db.session.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
	if model is None:
		return None
	model.status = WebhookEventStatus.PROCESSED
	model.processed_at = datetime.utcnow()
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def mark_failed(event_id, error_message):
	model = db.session.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
	if model is None:
		return None
	model.status = WebhookEventStatus.FAILED
	model.last_error = str(error_message)[:2000]
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def mark_ignored(event_id, reason):
	model = db.session.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
	if model is None:
		return None
	model.status = WebhookEventStatus.IGNORED
	model.last_error = reason
	model.updated_at = datetime.utcnow()
	db.session.commit()
	return model


def list_events(page=0, page_size=50, status=None, event_type=None):
	q = db.session.query(StripeWebhookEvent)
	if status:
		q = q.filter(StripeWebhookEvent.status == WebhookEventStatus[status])
	if event_type:
		q = q.filter(StripeWebhookEvent.event_type == event_type)
	total = q.count()
	items = q.order_by(StripeWebhookEvent.created_at.desc()).offset(page * page_size).limit(page_size).all()
	return items, total


def get_event(event_id):
	return db.session.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
