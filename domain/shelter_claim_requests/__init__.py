from math import ceil

import repository.shelter_claim_requests as claims_data
import repository.shelters as shelters_data
import repository.shelter_roles as shelter_roles_data
import domain.shelters as shelters_domain
import domain.users as users_domain
import domain.notifications as notifications_domain
from api.errors import BadRequest, NotFoundError, ForbiddenError
from utils.logger import logger, stringify

CLAIMABLE = {
    # (type, verification_status) pairs a normal user may request a claim on.
    # PENDING_CLAIM is included too: a different user may file a competing
    # claim while another user's claim on the same shelter is under review;
    # the duplicate guard only blocks the *same* user from double-filing.
    ("PERSONAL_WORKSPACE", "UNVERIFIED"),
    ("PERSONAL_WORKSPACE", "PENDING_CLAIM"),
    ("OFFICIAL_SHELTER", "UNVERIFIED"),
    ("OFFICIAL_SHELTER", "PENDING_CLAIM"),
}


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_requester(obj, info):
    return users_domain.get_user(obj["requester_user_id"])


def get_reviewed_by(obj, info):
    if not obj.get("reviewed_by"):
        return None
    return users_domain.get_user(obj["reviewed_by"])


# --- helpers ---
def shelter_id_for_claim(id):
    return claims_data.get_claim(id)["shelter_id"]


def _assert_claimable(shelter):
    key = (shelter.get("type"), shelter.get("verification_status"))
    if key not in CLAIMABLE:
        raise BadRequest(
            "only a PERSONAL_WORKSPACE or an UNVERIFIED OFFICIAL_SHELTER can be claimed"
        )


def _assert_pending(claim):
    if claim.get("status") != "PENDING":
        raise BadRequest("claim request is not pending")


# --- business ---
def _normalize_documents(proof_data):
    """Canonical shape for verification documents inside proof_data:
    {"documents": [{id, media_id, url, description, status, reviewer_note}]}.
    New/resubmitted documents are SUBMITTED with no reviewer note; media rows
    themselves are untouched (the media system stays as-is)."""
    import uuid as _uuid
    if not isinstance(proof_data, dict):
        return proof_data
    documents = proof_data.get("documents")
    if documents is None:
        return proof_data
    if not isinstance(documents, list) or len(documents) == 0:
        raise BadRequest("at least one verification document is required")
    normalized = []
    for doc in documents:
        if not isinstance(doc, dict) or not doc.get("media_id"):
            raise BadRequest("each document needs an uploaded media")
        if not (doc.get("description") or "").strip():
            raise BadRequest("each document needs a description")
        normalized.append({
            "id": doc.get("id") or f"{_uuid.uuid4()}",
            "media_id": doc["media_id"],
            "url": doc.get("url"),
            "description": doc["description"].strip(),
            "status": "SUBMITTED",
            "reviewer_note": None,
        })
    return {**proof_data, "documents": normalized}


def request_claim(shelter_id, data, actor_user_id):
    logger.domain(f"shelter_id: {shelter_id} data: {stringify(data)} by {actor_user_id}")
    try:
        shelter = shelters_domain.get_shelter(shelter_id)
        if shelter is None:
            raise NotFoundError(f"no shelter found with id {shelter_id}")
        _assert_claimable(shelter)
        if claims_data.get_pending_for_user_shelter(actor_user_id, shelter_id):
            raise BadRequest("a pending claim request already exists for this shelter")

        claim = claims_data.create_claim({
            "shelter_id": shelter_id,
            "requester_user_id": actor_user_id,
            "proof_data": _normalize_documents((data or {}).get("proof_data")),
            "message": (data or {}).get("message"),
        })
        # marks the shelter as under review; reverted if the claim doesn't succeed
        shelters_data.update_shelter(shelter_id, {"verification_status": "PENDING_CLAIM"})
        return claim
    except Exception as e:
        logger.error(e)
        raise e


def cancel_claim(id, actor_user_id):
    logger.domain(f"cancel claim {id} by {actor_user_id}")
    try:
        claim = claims_data.get_claim(id)
        _assert_pending(claim)
        if claim.get("requester_user_id") != actor_user_id:
            raise ForbiddenError("only the requester can cancel this claim")
        updated = claims_data.set_status(id, "CANCELLED")
        _revert_pending_claim_marker(claim["shelter_id"])
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def _revert_pending_claim_marker(shelter_id):
    """If nothing else is claiming this shelter, drop the PENDING_CLAIM marker
    back to UNVERIFIED so a future claim isn't blocked by a stale state."""
    shelter = shelters_domain.get_shelter(shelter_id)
    if shelter.get("verification_status") == "PENDING_CLAIM":
        shelters_data.update_shelter(shelter_id, {"verification_status": "UNVERIFIED"})


def approve_claim(id, decision_note, actor_user_id):
    logger.domain(f"approve claim {id} by {actor_user_id}")
    try:
        # late import: domain.shelter_roles imports domain.shelters
        import domain.shelter_roles as shelter_roles_domain
        import domain.shelter_ownerships as ownership_service

        claim = claims_data.get_claim(id)
        _assert_pending(claim)
        shelter_id = claim["shelter_id"]
        requester_id = claim["requester_user_id"]
        shelter = shelters_domain.get_shelter(shelter_id)

        shelters_data.update_shelter(shelter_id, {
            "type": "OFFICIAL_SHELTER",
            "verification_status": "VERIFIED",
        })

        # adjust any other technical OWNER: downgrade to MANAGER rather than remove
        adjusted_owner_id = None
        for row in shelter_roles_data.get_owner_role_models_for_shelter(shelter_id):
            if row.user_id != requester_id:
                shelter_roles_domain.update_shelter_role(row.id, {"role": "MANAGER"})
                adjusted_owner_id = row.user_id

        requester_roles = shelter_roles_data.get_roles_for_user_on_shelter(requester_id, shelter_id)
        if requester_roles:
            shelter_roles_domain.update_shelter_role(requester_roles[0]["id"], {"role": "OWNER"})
        else:
            shelter_roles_domain.create_shelter_role({
                "user_id": requester_id,
                "shelter_id": shelter_id,
                "role": "OWNER",
            })

        # technical ownership moves to the approved requester; the claim
        # supersedes any previous owner (e.g. the platform-imported creator)
        ownership_service.add_owner(
            shelter_id=shelter_id,
            user_id=requester_id,
            source="CLAIM_APPROVAL",
            created_by_id=actor_user_id,
        )
        for ownership in ownership_service.list_active_owners(shelter_id):
            if ownership["user_id"] != requester_id:
                ownership_service.remove_owner(
                    shelter_id=shelter_id,
                    user_id=ownership["user_id"],
                    actor_user_id=actor_user_id,
                    status="ENDED",
                )

        updated = claims_data.resolve_claim(id, "APPROVED", actor_user_id, decision_note)

        notifications_domain.notify_shelter_claim_decision(
            claim_id=id,
            user_id=requester_id,
            shelter_id=shelter_id,
            shelter_name=shelter.get("name"),
            approved=True,
            decision_note=decision_note,
            actor_user_id=actor_user_id,
        )
        if adjusted_owner_id:
            notifications_domain.notify_shelter_claim_decision(
                claim_id=id,
                user_id=adjusted_owner_id,
                shelter_id=shelter_id,
                shelter_name=shelter.get("name"),
                approved=True,
                decision_note=decision_note,
                actor_user_id=actor_user_id,
            )
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def reject_claim(id, decision_note, actor_user_id):
    logger.domain(f"reject claim {id} by {actor_user_id}")
    try:
        claim = claims_data.get_claim(id)
        _assert_pending(claim)
        shelter = shelters_domain.get_shelter(claim["shelter_id"])

        updated = claims_data.resolve_claim(id, "REJECTED", actor_user_id, decision_note)
        _revert_pending_claim_marker(claim["shelter_id"])

        notifications_domain.notify_shelter_claim_decision(
            claim_id=id,
            user_id=claim["requester_user_id"],
            shelter_id=claim["shelter_id"],
            shelter_name=shelter.get("name"),
            approved=False,
            decision_note=decision_note,
            actor_user_id=actor_user_id,
        )
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def update_claim_documents(id, documents, actor_user_id):
    """The requester replaces/fixes documents on a still-PENDING claim (e.g.
    after a reviewer asked for a change). Resubmitted documents go back to
    SUBMITTED and lose the reviewer note."""
    logger.domain(f"update documents on claim {id} by {actor_user_id}")
    try:
        claim = claims_data.get_claim(id)
        if claim.get("requester_user_id") != actor_user_id:
            raise ForbiddenError("only the requester can update this claim's documents")
        _assert_pending(claim)
        proof_data = _normalize_documents(
            {**(claim.get("proof_data") or {}), "documents": documents}
        )
        return claims_data.update_proof_data(id, proof_data)
    except Exception as e:
        logger.error(e)
        raise e


def request_document_change(id, document_id, note, actor_user_id):
    """A platform reviewer flags one document as not acceptable: the document
    goes CHANGE_REQUESTED with the reviewer note and the requester is
    notified so the app can offer the replacement flow."""
    logger.domain(f"request document change on claim {id} doc {document_id} by {actor_user_id}")
    try:
        claim = claims_data.get_claim(id)
        _assert_pending(claim)
        proof_data = dict(claim.get("proof_data") or {})
        documents = list(proof_data.get("documents") or [])
        target = next((d for d in documents if d.get("id") == document_id), None)
        if target is None:
            raise NotFoundError(f"no document {document_id} on claim {id}")
        target["status"] = "CHANGE_REQUESTED"
        target["reviewer_note"] = (note or "").strip() or None
        proof_data["documents"] = documents
        updated = claims_data.update_proof_data(id, proof_data)

        shelter = shelters_domain.get_shelter(claim["shelter_id"]) or {}
        notifications_domain.notify_shelter_claim_document_change(
            claim_id=id,
            user_id=claim["requester_user_id"],
            shelter_id=claim["shelter_id"],
            shelter_name=shelter.get("name"),
            document_id=document_id,
            note=target["reviewer_note"],
            actor_user_id=actor_user_id,
        )
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def get_claim(id):
    return claims_data.get_claim(id)


def list_my_claims(user_id, common_search):
    logger.domain(f"user_id: {user_id} common_search: {stringify(common_search)}")
    try:
        pagination = common_search.get("pagination", {"page": 0, "page_size": 20})
        items, total = claims_data.list_for_user(user_id, pagination)
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


def list_platform_claims(common_search):
    """Cross-tenant claim list for the back office (platform.claims.review)."""
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        items = claims_data.get_shelter_claims(common_search)
        total = claims_data.get_total_items(common_search)
        page_size = common_search["pagination"]["page_size"]
        return items, {
            "total_items": total,
            "total_pages": ceil(total / page_size) if page_size else 0,
            "current_page": common_search["pagination"]["page"],
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(e)
        raise e


def _inject_shelter_filter(common_search, shelter_id):
    filters = common_search.setdefault("filters", {})
    grp = filters.setdefault("and", {})
    fixed = grp.setdefault("fixed", {})
    fixed["shelter_id"] = shelter_id
    return common_search


def list_shelter_claims(shelter_id, common_search):
    logger.domain(f"shelter_id: {shelter_id} common_search: {stringify(common_search)}")
    try:
        _inject_shelter_filter(common_search, shelter_id)
        items = claims_data.get_shelter_claims(common_search)
        total = claims_data.get_total_items(common_search)
        page_size = common_search["pagination"]["page_size"]
        pagination = {
            "total_items": total,
            "total_pages": ceil(total / page_size) if page_size else 0,
            "current_page": common_search["pagination"]["page"],
            "page_size": page_size,
        }
        return items, pagination
    except Exception as e:
        logger.error(e)
        raise e
