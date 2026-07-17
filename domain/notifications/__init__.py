from math import ceil
from datetime import datetime, timedelta

import repository.notifications as notifications_data
from utils.logger import logger, stringify
from utils.dates import utc_now

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


# --- queries ---
def list_my_notifications(user_id, common_search):
    logger.domain(f"user_id: {user_id} common_search: {stringify(common_search)}")
    try:
        pagination = common_search.get("pagination", {"page": 0, "page_size": 20})
        items, total = notifications_data.list_my_notifications(user_id, pagination)
        page_size = pagination.get("page_size", 20) or 20
        return items, {
            "total_items": total,
            "total_pages": ceil(total / page_size) if page_size else 0,
            "current_page": pagination.get("page", 0),
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(e)
        raise e


def get_unread_count(user_id):
    return notifications_data.count_unread(user_id)


# --- mutations ---
def mark_as_read(id, user_id):
    return notifications_data.mark_as_read(id, user_id)


def mark_all_as_read(user_id):
    notifications_data.mark_all_as_read(user_id)
    return True


def dismiss(id, user_id):
    return notifications_data.dismiss(id, user_id)


def create_notification(data):
    logger.domain(f"data: {stringify(data)}")
    return notifications_data.create_notification(data)


# --- invite notifications (event-driven, idempotent via dedupe_key) ---
def notify_pet_ownership_invite(invite_id, user_id, pet_id, pet_name, role, actor_user_id):
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "PET_OWNERSHIP_INVITE",
        "priority": "HIGH",
        "title": f"Invitation to care for {pet_name}",
        "message": f"You have been invited as {role} for {pet_name}.",
        "entity_type": "OWNERSHIP",
        "entity_id": invite_id,
        "pet_id": pet_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/pets/detail/{pet_id}",
        "payload": {"role": role, "pet_name": pet_name},
        "dedupe_key": f"pet_ownership_invite:{invite_id}:{user_id}",
    })


def notify_shelter_invite(invite_id, user_id, shelter_id, shelter_name, role, actor_user_id):
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_INVITE",
        "priority": "HIGH",
        "title": f"Invitation to join {shelter_name}",
        "message": f"You have been invited as {role} at {shelter_name}.",
        "entity_type": "SHELTER_INVITE",
        "entity_id": invite_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {"role": role, "shelter_name": shelter_name},
        "dedupe_key": f"shelter_invite:{invite_id}:{user_id}",
    })


def notify_shelter_join_request(request_id, user_id, shelter_id, shelter_name, applicant_name, actor_user_id):
    """Tells one OWNER/MANAGER that someone applied as volunteer."""
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_JOIN_REQUEST",
        "priority": "HIGH",
        "title": f"Volunteer application for {shelter_name}",
        "message": f"{applicant_name} wants to join {shelter_name} as a volunteer.",
        "entity_type": "SHELTER_JOIN_REQUEST",
        "entity_id": request_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {"shelter_name": shelter_name, "applicant_name": applicant_name},
        "dedupe_key": f"shelter_join_request:{request_id}:{user_id}",
    })


def notify_shelter_join_decision(request_id, user_id, shelter_id, shelter_name, approved, actor_user_id):
    """Tells the applicant the outcome of their volunteer application."""
    title = (
        f"Application approved for {shelter_name}" if approved
        else f"Application rejected for {shelter_name}"
    )
    message = (
        f"Your volunteer application for {shelter_name} was approved. Welcome!"
        if approved else
        f"Your volunteer application for {shelter_name} was rejected."
    )
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_JOIN_REQUEST",
        "priority": "HIGH",
        "title": title,
        "message": message,
        "entity_type": "SHELTER_JOIN_REQUEST",
        "entity_id": request_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {"shelter_name": shelter_name, "approved": approved},
        "dedupe_key": f"shelter_join_decision:{request_id}:{user_id}",
    })


def notify_donation_received(donation_id, user_id, shelter_id, shelter_name,
                             amount_cents, currency, pet_name=None, is_test=False):
    """Tells one shelter member that a donation came in — amount plus
    whether it went to a specific pet or to the shelter itself."""
    amount = f"{amount_cents / 100:.2f} {currency.upper()}"
    target = f"for {pet_name}" if pet_name else f"to {shelter_name}"
    prefix = "[TEST] " if is_test else ""
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "DONATION_RECEIVED",
        "priority": "NORMAL",
        "title": f"{prefix}New donation {target}",
        "message": f"{prefix}{amount} donated {target}.",
        "entity_type": "DONATION",
        "entity_id": donation_id,
        "shelter_id": shelter_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {
            "shelter_name": shelter_name,
            "pet_name": pet_name,
            "amount_cents": amount_cents,
            "currency": currency,
            "is_test": is_test,
        },
        "dedupe_key": f"donation_received:{donation_id}:{user_id}",
    })


def notify_shelter_ownership_transfer(transfer_id, user_id, shelter_id, shelter_name, actor_user_id):
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_OWNERSHIP_TRANSFER",
        "priority": "HIGH",
        "title": f"Ownership transfer for {shelter_name}",
        "message": f"You have been asked to become the owner of {shelter_name}.",
        "entity_type": "SHELTER_OWNERSHIP_TRANSFER",
        "entity_id": transfer_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {"shelter_name": shelter_name},
        "dedupe_key": f"shelter_ownership_transfer:{transfer_id}:{user_id}",
    })


def notify_shelter_claim_decision(claim_id, user_id, shelter_id, shelter_name, approved, decision_note, actor_user_id):
    title = f"Claim approved for {shelter_name}" if approved else f"Claim rejected for {shelter_name}"
    message = (
        f"Your claim request for {shelter_name} was approved."
        if approved else
        f"Your claim request for {shelter_name} was rejected."
    )
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_CLAIM_REQUEST",
        "priority": "HIGH",
        "title": title,
        "message": message,
        "entity_type": "SHELTER_CLAIM_REQUEST",
        "entity_id": claim_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}",
        "payload": {"shelter_name": shelter_name, "approved": approved, "decision_note": decision_note},
        "dedupe_key": f"shelter_claim_decision:{claim_id}:{user_id}",
    })


def notify_shelter_claim_document_change(claim_id, user_id, shelter_id, shelter_name,
                                         document_id, note, actor_user_id):
    """A reviewer asked to replace one verification document. Reuses the
    SHELTER_CLAIM_REQUEST type (no enum migration); the app branches on
    payload.kind to open the document-replacement flow."""
    title = f"Document update requested for {shelter_name}"
    message = (
        f"A reviewer asked you to replace a verification document for {shelter_name}."
        + (f" Note: {note}" if note else "")
    )
    return notifications_data.create_if_absent({
        "user_id": user_id,
        "type": "SHELTER_CLAIM_REQUEST",
        "priority": "HIGH",
        "title": title,
        "message": message,
        "entity_type": "SHELTER_CLAIM_REQUEST",
        "entity_id": claim_id,
        "shelter_id": shelter_id,
        "actor_user_id": actor_user_id,
        "action_url": f"/shelters/detail/{shelter_id}/verification",
        "payload": {
            "kind": "DOCUMENT_CHANGE_REQUESTED",
            "shelter_name": shelter_name,
            "document_id": document_id,
            "note": note,
        },
        # per-document dedupe: a second change request on the same document
        # replaces nothing but a different document notifies again
        "dedupe_key": f"shelter_claim_doc_change:{claim_id}:{document_id}",
    })


# --- cron generation (idempotent via dedupe_key) ---
def generate_treatment_reminders(target_date=None):
    """One TREATMENT_REMINDER per owner for each vaccine/operation/antiparasitic
    due on target_date (default: today). Idempotent per treatment per day."""
    if target_date is None:
        target_date = utc_now().date()
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)
    day_str = target_date.strftime("%Y-%m-%d")
    created = 0
    try:
        for tr in notifications_data.get_due_treatments(day_start, day_end):
            owner_ids = notifications_data.get_owner_ids_for_pet(tr["pet_id"])
            for uid in dict.fromkeys(owner_ids):
                row = notifications_data.create_if_absent({
                    "user_id": uid,
                    "type": "TREATMENT_REMINDER",
                    "priority": "HIGH",
                    "title": f"{tr['treatment_name']} due for {tr['pet_name']}",
                    "message": f"{tr['pet_name']} has a {tr['treatment_type']} scheduled today.",
                    "entity_type": "TREATMENT",
                    "entity_id": tr["treatment_id"],
                    "pet_id": tr["pet_id"],
                    "action_url": f"/pets/{tr['pet_id']}",
                    "payload": {
                        "treatment_name": tr["treatment_name"],
                        "treatment_type": tr["treatment_type"],
                        "pet_name": tr["pet_name"],
                    },
                    "dedupe_key": f"TREATMENT_REMINDER:{tr['treatment_id']}:{uid}:{day_str}",
                    "scheduled_at": day_start.strftime(DATE_FMT),
                })
                if row is not None:
                    created += 1
        logger.check(f"generated {created} treatment reminder notification(s)")
        return created
    except Exception as e:
        logger.error(e)
        raise e


def generate_pet_birthdays(target_date=None):
    """One PET_BIRTHDAY per owner for each pet whose birthday falls on
    target_date (default: today). Idempotent per pet per year."""
    if target_date is None:
        target_date = utc_now().date()
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    created = 0
    try:
        for pet in notifications_data.get_pets_with_birthday(target_date.month, target_date.day):
            owner_ids = notifications_data.get_owner_ids_for_pet(pet["pet_id"])
            for uid in dict.fromkeys(owner_ids):
                row = notifications_data.create_if_absent({
                    "user_id": uid,
                    "type": "PET_BIRTHDAY",
                    "priority": "LOW",
                    "title": f"Happy birthday to {pet['pet_name']}!",
                    "message": f"{pet['pet_name']} is celebrating a birthday today.",
                    "entity_type": "PET",
                    "entity_id": pet["pet_id"],
                    "pet_id": pet["pet_id"],
                    "action_url": f"/pets/{pet['pet_id']}",
                    "payload": {"pet_name": pet["pet_name"]},
                    "dedupe_key": f"PET_BIRTHDAY:{pet['pet_id']}:{uid}:{target_date.year}",
                    "scheduled_at": day_start.strftime(DATE_FMT),
                })
                if row is not None:
                    created += 1
        logger.check(f"generated {created} pet birthday notification(s)")
        return created
    except Exception as e:
        logger.error(e)
        raise e
