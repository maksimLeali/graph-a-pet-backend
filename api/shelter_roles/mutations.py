from ariadne import convert_kwargs_to_snake_case
from domain.shelter_roles import create_shelter_role, update_shelter_role, delete_shelter_role
from domain.shelter_roles import get_shelter_role as get_shelter_role_domain
from domain.authorization import invalidate_request_cache
from domain.authorization.catalog import ShelterPermissions
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token
from api.errors import format_error, ForbiddenError
from utils.logger import logger, stringify
from utils import get_request_user


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_role_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        # security fix: era solo-auth — chiunque poteva autoassegnarsi OWNER.
        # Ora richiede shelters.roles.assign sullo shelter target; assegnare
        # OWNER (= ownership tecnica legacy) richiede in più
        # shelters.ownership.transfer.
        token = info.context.headers['authorization']
        shelter_id = (data or {}).get('shelter_id')
        if not shelter_id:
            raise ForbiddenError("shelter_id required for authorization")
        authorize_from_token(token, ShelterPermissions.ROLES_ASSIGN, shelter_id)
        if (data or {}).get('role') == "OWNER":
            authorize_from_token(
                token, ShelterPermissions.OWNERSHIP_TRANSFER, shelter_id
            )
        shelter_role = create_shelter_role(data)
        invalidate_request_cache()
        payload = {
            "success": True,
            "shelter_role": shelter_role,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_role_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        # security fix: era solo-auth. Lo shelter è ricavato dall'entità (mai
        # dal client); serve shelters.roles.manage, e ownership.transfer per
        # promuovere a OWNER.
        token = info.context.headers['authorization']
        existing = get_shelter_role_domain(id)
        shelter_id = existing["shelter_id"]
        authorize_from_token(token, ShelterPermissions.ROLES_MANAGE, shelter_id)
        if (data or {}).get('role') == "OWNER" and existing.get("role") != "OWNER":
            authorize_from_token(
                token, ShelterPermissions.OWNERSHIP_TRANSFER, shelter_id
            )
        shelter_role = update_shelter_role(id, data)
        invalidate_request_cache()
        payload = {
            "success": True,
            "shelter_role": shelter_role,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "shelter_role": None,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def delete_shelter_role_resolver(obj, info, id):
    logger.api(f"id {id} remove")
    try:
        # lo shelter viene dall'entità; rimuovere un ruolo richiede
        # shelters.roles.manage (rimuovere un OWNER richiede ownership.transfer)
        token = info.context.headers['authorization']
        existing = get_shelter_role_domain(id)
        authorize_from_token(token, ShelterPermissions.ROLES_MANAGE, existing["shelter_id"])
        if existing.get("role") == "OWNER":
            authorize_from_token(
                token, ShelterPermissions.OWNERSHIP_TRANSFER, existing["shelter_id"]
            )
        current_user = get_request_user(token)
        memoriae_id = delete_shelter_role(id, current_user['id'])
        invalidate_request_cache()
        payload = {
            "success": True,
            "id": memoriae_id,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload
