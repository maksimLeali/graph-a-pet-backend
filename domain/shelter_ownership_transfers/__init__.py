from math import ceil
from datetime import datetime

import repository.shelter_ownership_transfers as transfers_data
import repository.shelter_roles as shelter_roles_data
import domain.shelters as shelters_domain
import domain.users as users_domain
import domain.damnationes_memoriae as damnatio_domain
import domain.notifications as notifications_domain
from api.errors import BadRequest, NotFoundError, ForbiddenError
from utils.logger import logger, stringify
from utils.dates import utc_now


# --- field resolvers ---
def get_shelter(obj, info):
    return shelters_domain.get_shelter(obj["shelter_id"])


def get_from_user(obj, info):
    return users_domain.get_user(obj["from_user_id"])


def get_to_user(obj, info):
    return users_domain.get_user(obj["to_user_id"])


# --- helpers ---
def shelter_id_for_transfer(id):
    return transfers_data.get_transfer(id)["shelter_id"]


def _expire_if_due(transfer):
    """Lazily flips a stale PENDING transfer to EXPIRED. Returns the (possibly
    updated) transfer dict."""
    if transfer.get("status") != "PENDING" or not transfer.get("expires_at"):
        return transfer
    expires_at = transfer["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    if utc_now() >= expires_at:
        return transfers_data.set_status(transfer["id"], "EXPIRED")
    return transfer


def _assert_pending(transfer):
    if transfer.get("status") != "PENDING":
        raise BadRequest("transfer is not pending")


# --- business ---
def request_transfer(shelter_id, to_user_id, new_role_for_previous_owner, actor_user_id):
    logger.domain(
        f"shelter_id: {shelter_id} to: {to_user_id} "
        f"new_role: {new_role_for_previous_owner} by {actor_user_id}"
    )
    try:
        import domain.shelter_ownerships as ownership_service
        if not ownership_service.is_active_owner(actor_user_id, shelter_id):
            # transition fallback: shelters created before the ownership
            # backfill still track ownership in legacy shelter_roles
            if shelter_roles_data.get_owner_role_model(actor_user_id, shelter_id) is None:
                raise ForbiddenError("only the current owner can request an ownership transfer")
        if to_user_id == actor_user_id:
            raise BadRequest("cannot transfer ownership to yourself")
        destination = users_domain.get_user(to_user_id)
        if destination is None:
            raise NotFoundError(f"no user found with id {to_user_id}")
        if transfers_data.get_pending_for_shelter(shelter_id):
            raise BadRequest("a pending ownership transfer already exists for this shelter")

        transfer = transfers_data.create_transfer({
            "shelter_id": shelter_id,
            "from_user_id": actor_user_id,
            "to_user_id": to_user_id,
            "new_role_for_previous_owner": new_role_for_previous_owner,
        })

        shelter = shelters_domain.get_shelter(shelter_id)
        notifications_domain.notify_shelter_ownership_transfer(
            transfer_id=transfer["id"],
            user_id=to_user_id,
            shelter_id=shelter_id,
            shelter_name=shelter.get("name"),
            actor_user_id=actor_user_id,
        )
        return transfer
    except Exception as e:
        logger.error(e)
        raise e


def accept_transfer(id, actor_user_id):
    logger.domain(f"accept transfer {id} by {actor_user_id}")
    try:
        # late import: domain.shelter_roles imports domain.shelters, and this
        # module is imported by domain.shelters-adjacent flows too
        import domain.shelter_roles as shelter_roles_domain
        import domain.shelter_ownerships as ownership_service

        transfer = _expire_if_due(transfers_data.get_transfer(id))
        _assert_pending(transfer)
        if transfer.get("to_user_id") != actor_user_id:
            raise ForbiddenError("only the invited user can accept this transfer")

        shelter_id = transfer["shelter_id"]
        to_user_id = transfer["to_user_id"]
        from_user_id = transfer["from_user_id"]
        new_role_for_previous_owner = transfer.get("new_role_for_previous_owner")

        # destination becomes OWNER: reuse an existing role row if present,
        # otherwise create one
        existing_roles = shelter_roles_data.get_roles_for_user_on_shelter(to_user_id, shelter_id)
        if existing_roles:
            shelter_roles_domain.update_shelter_role(existing_roles[0]["id"], {"role": "OWNER"})
        else:
            shelter_roles_domain.create_shelter_role({
                "user_id": to_user_id,
                "shelter_id": shelter_id,
                "role": "OWNER",
            })

        # previous owner: downgrade or remove, per the option chosen at request time
        previous_owner_role = shelter_roles_data.get_owner_role_model(from_user_id, shelter_id)
        if previous_owner_role is not None:
            if new_role_for_previous_owner:
                shelter_roles_domain.update_shelter_role(
                    previous_owner_role.id, {"role": new_role_for_previous_owner}
                )
            else:
                damnatio_domain.delete_row(
                    previous_owner_role.id, 'shelter_roles',
                    previous_owner_role.to_dict(), actor_user_id,
                )

        # technical ownership moves atomically; the previous owner may keep an
        # RBAC role on the shelter but never keeps ownership
        if ownership_service.is_active_owner(from_user_id, shelter_id):
            ownership_service.transfer_ownership(
                shelter_id=shelter_id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                actor_user_id=actor_user_id,
            )
        else:
            # legacy transfer created before the ownership backfill ran
            ownership_service.add_owner(
                shelter_id=shelter_id,
                user_id=to_user_id,
                source="OWNERSHIP_TRANSFER",
                created_by_id=actor_user_id,
            )

        return transfers_data.set_status(id, "ACCEPTED", "accepted_at")
    except Exception as e:
        logger.error(e)
        raise e


def reject_transfer(id, actor_user_id):
    logger.domain(f"reject transfer {id} by {actor_user_id}")
    try:
        transfer = _expire_if_due(transfers_data.get_transfer(id))
        _assert_pending(transfer)
        if transfer.get("to_user_id") != actor_user_id:
            raise ForbiddenError("only the invited user can reject this transfer")
        return transfers_data.set_status(id, "REJECTED", "rejected_at")
    except Exception as e:
        logger.error(e)
        raise e


def cancel_transfer(id, actor_user_id):
    logger.domain(f"cancel transfer {id} by {actor_user_id}")
    try:
        transfer = transfers_data.get_transfer(id)
        _assert_pending(transfer)
        if transfer.get("from_user_id") != actor_user_id:
            raise ForbiddenError("only the requester can cancel this transfer")
        return transfers_data.set_status(id, "CANCELLED", "cancelled_at")
    except Exception as e:
        logger.error(e)
        raise e


def get_transfer(id):
    return transfers_data.get_transfer(id)


def list_my_transfers(user_id, common_search):
    logger.domain(f"user_id: {user_id} common_search: {stringify(common_search)}")
    try:
        pagination = common_search.get("pagination", {"page": 0, "page_size": 20})
        items, total = transfers_data.list_for_user(user_id, pagination)
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


def _inject_shelter_filter(common_search, shelter_id):
    filters = common_search.setdefault("filters", {})
    grp = filters.setdefault("and", {})
    fixed = grp.setdefault("fixed", {})
    fixed["shelter_id"] = shelter_id
    return common_search


def list_shelter_transfers(shelter_id, common_search):
    logger.domain(f"shelter_id: {shelter_id} common_search: {stringify(common_search)}")
    try:
        _inject_shelter_filter(common_search, shelter_id)
        items = transfers_data.get_shelter_transfers(common_search)
        total = transfers_data.get_total_items(common_search)
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
