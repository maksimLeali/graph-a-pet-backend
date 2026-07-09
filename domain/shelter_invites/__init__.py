import repository.shelter_invites as shelter_invites_data
import repository.shelter_roles as shelter_roles_data
import domain.users as users_domain
import domain.shelters as shelters_domain
import domain.notifications as notifications_domain
from api.errors import BadRequest, NotFoundError, ForbiddenError
from utils.logger import logger, stringify


# --- field resolvers ---
def get_user(obj, info):
    return users_domain.get_user(obj["user_id"])


def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_invited_by(obj, info):
    if not obj.get("invited_by_id"):
        return None
    return users_domain.get_user(obj["invited_by_id"])


# --- business ---
def create_shelter_invite(data, actor_user_id):
    logger.domain(f"data: {stringify(data)} by {actor_user_id}")
    try:
        user = users_domain.get_user(data.get("user_id"))
        if user is None:
            raise NotFoundError(f'no user found with id {data.get("user_id")}')
        shelter = shelters_domain.get_shelter(data.get("shelter_id"))
        if shelter is None:
            raise NotFoundError(f'no shelter found with id {data.get("shelter_id")}')
        if data.get("role") is None:
            raise BadRequest("missing role")
        # avoid stacking duplicate pending invites for the same user+shelter
        existing = shelter_invites_data.get_pending_for_user_shelter(
            data.get("user_id"), data.get("shelter_id")
        )
        if existing:
            invite = existing[0]
        else:
            invite = shelter_invites_data.create_shelter_invite({
                "shelter_id": data.get("shelter_id"),
                "user_id": data.get("user_id"),
                "role": data.get("role"),
                "status": "PENDING",
                "invited_by_id": actor_user_id,
            })
        notifications_domain.notify_shelter_invite(
            invite_id=invite["id"],
            user_id=invite["user_id"],
            shelter_id=invite["shelter_id"],
            shelter_name=shelter.get("name"),
            role=invite["role"],
            actor_user_id=actor_user_id,
        )
        return invite
    except Exception as e:
        logger.error(e)
        raise e


def _load_own_pending(id, user_id):
    invite = shelter_invites_data.get_shelter_invite(id)
    if invite.get("user_id") != user_id:
        raise ForbiddenError("only the invited user can respond to this invite")
    if invite.get("status") != "PENDING":
        raise BadRequest("invite is not pending")
    return invite


def accept_shelter_invite(id, user_id):
    logger.domain(f"accept shelter invite {id} by {user_id}")
    try:
        invite = _load_own_pending(id, user_id)
        # accept/reject logic stays backend-side: creates the real ShelterRole
        shelter_roles_data.create_shelter_role({
            "user_id": invite["user_id"],
            "shelter_id": invite["shelter_id"],
            "role": invite["role"],
        })
        return shelter_invites_data.set_status(id, "ACCEPTED")
    except Exception as e:
        logger.error(e)
        raise e


def reject_shelter_invite(id, user_id):
    logger.domain(f"reject shelter invite {id} by {user_id}")
    try:
        _load_own_pending(id, user_id)
        return shelter_invites_data.set_status(id, "REJECTED")
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_invite(id):
    return shelter_invites_data.get_shelter_invite(id)
