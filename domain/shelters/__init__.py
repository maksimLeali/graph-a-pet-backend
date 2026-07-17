import repository.shelters as shelters_data
import repository.medias as medias_data
from math import ceil
from utils.logger import logger, stringify
from utils.html_sanitize import sanitize_html
from api.errors import ForbiddenError
import domain.damnationes_memoriae as damnatio_domain
import pydash as py_


SHELTER_UPDATE_FIELDS = [
    "name", "street", "street_number", "city",
    "province_code", "postal_code", "region", "district", "contacts",
    "public_description", "public_story_html", "public_contact_email", "public_contact_phone",
    "accepts_volunteers", "public_location_label", "public_lat", "public_lng",
]

# scope used for the first shelter_images media, shown as the public logo
SHELTER_LOGO_SCOPE = "shelter_images"

PERSONAL_WORKSPACE_ADDRESS_FIELDS = [
    "street", "street_number", "city", "province_code", "postal_code",
]


def _assert_visibility_allowed(visibility, verification_status, actor_user):
    """PUBLIC visibility requires the shelter to be verified, unless the actor
    is a global admin (manual approval)."""
    if visibility != "PUBLIC":
        return
    from domain.authorization import authorization_service
    from domain.authorization.catalog import PlatformPermissions
    can_verify = bool(actor_user) and authorization_service.can(
        actor_user.get("id"), PlatformPermissions.SHELTERS_VERIFY
    )
    if verification_status != "VERIFIED" and not can_verify:
        raise ForbiddenError("PUBLIC visibility requires a verified shelter or admin approval")


def create_shelter(data, actor_user=None):
    logger.domain(f"data: {stringify(data)}")
    try:
        visibility = data.get("visibility") or "PUBLIC"
        verification_status = data.get("verification_status") or "VERIFIED"
        _assert_visibility_allowed(visibility, verification_status, actor_user)
        shelter = shelters_data.create_shelter(data)
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def create_personal_workspace(data, current_user_id):
    """A private space for a normal user, not presented as an official
    shelter: PERSONAL_WORKSPACE / UNVERIFIED / PRIVATE, creator becomes OWNER."""
    logger.domain(f"data: {stringify(data)} by {current_user_id}")
    try:
        # late import: domain.shelter_roles imports domain.shelters
        import domain.shelter_roles as shelter_roles_domain
        import domain.shelter_ownerships as ownership_service
        payload = dict(data)
        for field in PERSONAL_WORKSPACE_ADDRESS_FIELDS:
            payload.setdefault(field, "")
        payload["type"] = "PERSONAL_WORKSPACE"
        payload["verification_status"] = "UNVERIFIED"
        payload["visibility"] = "PRIVATE"
        shelter = shelters_data.create_shelter(payload)
        shelter_roles_domain.create_shelter_role({
            "user_id": current_user_id,
            "shelter_id": shelter["id"],
            "role": "OWNER",
        })
        ownership_service.add_owner(
            shelter_id=shelter["id"],
            user_id=current_user_id,
            source="WORKSPACE_CREATOR",
            created_by_id=current_user_id,
        )
        logger.check(f"personal workspace: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def update_shelter(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        payload = py_.pick(data, SHELTER_UPDATE_FIELDS)
        # rich text is user-authored and shown to external users — sanitize at
        # this trusted write boundary so render sites can trust the stored value
        if "public_story_html" in payload:
            payload["public_story_html"] = sanitize_html(payload["public_story_html"])
        shelter = shelters_data.update_shelter(id, payload)
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def delete_shelter(id, user_id):
    logger.domain(f"id {id} remove")
    try:
        shelter = shelters_data.get_shelter(id)
        damnatio_id = damnatio_domain.delete_row(id, 'shelters', shelter, user_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_shelters(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        shelters = get_shelters(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (shelters, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelters(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        shelters = shelters_data.get_shelters(common_search)
        logger.output(f"shelters: {len(shelters)}")
        return shelters
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter(id):
    logger.domain(f"id: {id}")
    try:
        shelter = shelters_data.get_shelter(id)
        logger.check(f"shelter: {stringify(shelter)}")
        return shelter
    except Exception as e:
        logger.error(e)
        raise e


def _to_public_shelter(shelter):
    return {
        "id": shelter["id"],
        "name": shelter["name"],
        "city": shelter.get("city"),
        "region": shelter.get("region"),
        "public_description": shelter.get("public_description"),
        "public_story_html": shelter.get("public_story_html"),
        "public_contact_email": shelter.get("public_contact_email"),
        "public_contact_phone": shelter.get("public_contact_phone"),
        "logo_media_id": medias_data.get_first_media_id(shelter["id"], SHELTER_LOGO_SCOPE),
        "accepts_volunteers": bool(shelter.get("accepts_volunteers")),
        "public_location_label": shelter.get("public_location_label"),
        "public_lat": shelter.get("public_lat"),
        "public_lng": shelter.get("public_lng"),
    }


def discover_shelters(search):
    """Public shelter discovery: only PUBLIC + VERIFIED shelters, projected
    onto the dedicated PublicShelter shape (no roles/pets/operational data)."""
    logger.domain(f"search: {stringify(search)}")
    try:
        search = search or {}
        page = search.get("page", 0)
        page_size = search.get("page_size", 20)
        rows, total = shelters_data.get_public_shelters(
            search.get("name"),
            search.get("city"),
            search.get("province_code"),
            search.get("accepts_volunteers"),
            page,
            page_size,
        )
        items = [_to_public_shelter(row) for row in rows]
        pagination = {
            "total_items": total,
            "total_pages": ceil(total / page_size) if page_size else 0,
            "current_page": page,
            "page_size": page_size,
        }
        return items, pagination
    except Exception as e:
        logger.error(e)
        raise e


def get_public_shelter(id):
    logger.domain(f"id: {id}")
    try:
        shelter = shelters_data.get_public_shelter(id)
        if not shelter:
            return None
        return _to_public_shelter(shelter)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = shelters_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        pagination = {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
        }
        logger.output(f"pagination: {stringify(pagination)}")
        return pagination
    except Exception as e:
        logger.error(e)
        raise e
