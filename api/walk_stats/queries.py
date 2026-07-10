from ariadne import convert_kwargs_to_snake_case

import domain.walk_stats as walk_stats_domain
import domain.ownerships as ownerships_domain
import domain.shelter_pets as shelter_pets_domain
from api.middlewares import auth_middleware, assert_shelter_role
from api.errors import format_error, ForbiddenError
from utils import get_request_user
from utils.logger import logger

_ALLOWED_CUSTODY = {"OWNER", "SUB_OWNER", "PET_SITTER"}


def _assert_pet_custody(token, pet_id):
    current_user = get_request_user(token)
    ownerships = ownerships_domain.get_ownerships_for_user_pet(current_user["id"], pet_id)
    mine = any(o["custody_level"] in _ALLOWED_CUSTODY for o in ownerships)
    if not mine:
        raise ForbiddenError("no custody of this pet")


@convert_kwargs_to_snake_case
@auth_middleware
def get_pet_walking_stats_resolver(obj, info, pet_id, period):
    logger.api(f"pet_id: {pet_id} period: {period}")
    try:
        token = info.context.headers['authorization']
        _assert_pet_custody(token, pet_id)
        chart = walk_stats_domain.get_pet_walking_stats(pet_id, period)
        return {"success": True, "chart": chart}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_pet_walking_stats_resolver(obj, info, shelter_pet_id, period):
    logger.api(f"shelter_pet_id: {shelter_pet_id} period: {period}")
    try:
        token = info.context.headers['authorization']
        shelter_pet = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        assert_shelter_role(token, shelter_pet["shelter_id"], "STAFF")
        chart = walk_stats_domain.get_shelter_pet_walking_stats(shelter_pet_id, period)
        return {"success": True, "chart": chart}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
