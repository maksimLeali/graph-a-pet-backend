from ariadne import convert_kwargs_to_snake_case
import domain.shelter_invites as shelter_invites_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from utils.logger import logger


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_invite_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        invite = shelter_invites_domain.get_shelter_invite(id)
        return {"success": True, "shelter_invite": invite}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "shelter_invite": None,
        }
