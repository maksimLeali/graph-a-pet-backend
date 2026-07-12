from ariadne import convert_kwargs_to_snake_case

from api.errors import AuthenticationError, format_error
from domain.authorization import authorization_service
from utils import get_request_user
from utils.logger import logger


@convert_kwargs_to_snake_case
def my_shelter_authorization_resolver(obj, info, shelter_id):
    """Effective permissions + membership status of the caller on one shelter.
    The frontend consumes this instead of deriving capabilities from role names."""
    logger.api(f"shelter_id: {shelter_id}")
    token = info.context.headers.get("authorization")
    try:
        try:
            user = get_request_user(token)
        except Exception:
            raise AuthenticationError("unauthorized")
        permissions = authorization_service.effective_permissions(
            user["id"], shelter_id=shelter_id
        )
        return {
            "success": True,
            "authorization": {
                "shelter_id": shelter_id,
                "membership_status": authorization_service.membership_status(
                    user["id"], shelter_id
                ),
                "permissions": sorted(permissions),
            },
        }
    except Exception as e:
        logger.error(e)
        return {"success": False, "error": format_error(e, token)}
