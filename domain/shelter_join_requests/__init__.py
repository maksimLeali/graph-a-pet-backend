"""Volunteer application flow (user -> shelter, mirror of shelter_invites).

A user applies from the shelter's public page; every OWNER/MANAGER gets a
SHELTER_JOIN_REQUEST notification and can approve or reject. Approval
creates the real VOLUNTEER ShelterRole — the decision endpoints enforce
OWNER/MANAGER membership themselves because the GraphQL layer only has
the request id, not the shelter_id.
"""
import domain.notifications as notifications_domain
import domain.shelters as shelters_domain
import domain.users as users_domain
import repository.shelter_join_requests as join_requests_data
import repository.shelter_roles as shelter_roles_data
from api.errors import BadRequest, ForbiddenError, NotFoundError
from utils.logger import logger, stringify

def _assert_reviewer(user_id, shelter_id):
    from domain.authorization import authorization_service
    from domain.authorization.catalog import ShelterPermissions
    if not authorization_service.can(
        user_id, ShelterPermissions.MEMBERS_INVITE, shelter_id=shelter_id
    ):
        raise ForbiddenError("reviewing join requests requires shelters.members.invite")


def apply_as_volunteer(shelter_id, user_id, message=None):
    logger.domain(f"shelter_id: {shelter_id} user_id: {user_id}")
    try:
        shelter = shelters_domain.get_shelter(shelter_id)
        if shelter is None:
            raise NotFoundError(f"no shelter found with id {shelter_id}")
        if not shelter.get("accepts_volunteers"):
            raise BadRequest("this shelter is not accepting volunteers")
        import repository.authorization as authz_data
        membership = authz_data.get_membership(user_id, shelter_id)
        if membership and membership["status"] == "ACTIVE":
            raise BadRequest("you are already a member of this shelter")

        # idempotent: re-applying while pending returns the same request
        existing = join_requests_data.get_pending_for_user_shelter(user_id, shelter_id)
        if existing:
            return existing[0]

        join_request = join_requests_data.create_join_request({
            "shelter_id": shelter_id,
            "user_id": user_id,
            "message": message,
        })

        applicant = users_domain.get_user(user_id) or {}
        applicant_name = (
            " ".join(filter(None, [applicant.get("first_name"), applicant.get("last_name")]))
            or applicant.get("email")
            or "Someone"
        )
        import repository.authorization as authz_data
        from domain.authorization.catalog import ShelterPermissions
        reviewer_ids = authz_data.get_user_ids_with_permission_on_shelter(
            shelter_id, ShelterPermissions.MEMBERS_INVITE
        )
        for reviewer_id in reviewer_ids:
            notifications_domain.notify_shelter_join_request(
                request_id=join_request["id"],
                user_id=reviewer_id,
                shelter_id=shelter_id,
                shelter_name=shelter.get("name"),
                applicant_name=applicant_name,
                actor_user_id=user_id,
            )
        return join_request
    except Exception as e:
        logger.error(e)
        raise e


def _load_pending_for_review(id, reviewer_user_id):
    join_request = join_requests_data.get_join_request(id)
    _assert_reviewer(reviewer_user_id, join_request["shelter_id"])
    if join_request.get("status") != "PENDING":
        raise BadRequest("join request is not pending")
    return join_request


def approve_join_request(id, reviewer_user_id):
    logger.domain(f"approve join request {id} by {reviewer_user_id}")
    try:
        join_request = _load_pending_for_review(id, reviewer_user_id)
        shelter_roles_data.create_shelter_role({
            "user_id": join_request["user_id"],
            "shelter_id": join_request["shelter_id"],
            "role": "VOLUNTEER",
        })
        updated = join_requests_data.set_status(id, "APPROVED", reviewed_by=reviewer_user_id)
        shelter = shelters_domain.get_shelter(join_request["shelter_id"]) or {}
        notifications_domain.notify_shelter_join_decision(
            request_id=id,
            user_id=join_request["user_id"],
            shelter_id=join_request["shelter_id"],
            shelter_name=shelter.get("name"),
            approved=True,
            actor_user_id=reviewer_user_id,
        )
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def reject_join_request(id, reviewer_user_id):
    logger.domain(f"reject join request {id} by {reviewer_user_id}")
    try:
        join_request = _load_pending_for_review(id, reviewer_user_id)
        updated = join_requests_data.set_status(id, "REJECTED", reviewed_by=reviewer_user_id)
        shelter = shelters_domain.get_shelter(join_request["shelter_id"]) or {}
        notifications_domain.notify_shelter_join_decision(
            request_id=id,
            user_id=join_request["user_id"],
            shelter_id=join_request["shelter_id"],
            shelter_name=shelter.get("name"),
            approved=False,
            actor_user_id=reviewer_user_id,
        )
        return updated
    except Exception as e:
        logger.error(e)
        raise e


def get_join_request(id):
    return join_requests_data.get_join_request(id)


def get_my_join_request(shelter_id, user_id):
    """The caller's own pending request on shelter_id, or None — used by the
    public shelter page to render the button state."""
    pending = join_requests_data.get_pending_for_user_shelter(user_id, shelter_id)
    return pending[0] if pending else None


def list_join_requests_for_shelter(shelter_id, reviewer_user_id, status=None):
    logger.domain(f"list join requests for {shelter_id} by {reviewer_user_id}")
    try:
        _assert_reviewer(reviewer_user_id, shelter_id)
        return join_requests_data.list_for_shelter(shelter_id, status=status)
    except Exception as e:
        logger.error(e)
        raise e
