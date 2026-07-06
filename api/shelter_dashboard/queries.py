from ariadne import convert_kwargs_to_snake_case
import domain.shelter_dashboard as dashboard_domain
from api.errors import format_error
from api.middlewares import auth_middleware, assert_shelter_role
from utils.logger import logger


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_operational_dashboard_resolver(obj, info, shelter_id):
    logger.api(f"shelter_id: {shelter_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_id, "STAFF")
        dashboard = dashboard_domain.get_operational_dashboard(shelter_id)
        payload = {"success": True, "dashboard": dashboard}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "dashboard": None,
        }
    return payload
