from ariadne import convert_kwargs_to_snake_case
import domain.shelter_dashboard as dashboard_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from api.permissions import assert_capability, Cap
from utils.logger import logger


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_operational_dashboard_resolver(obj, info, shelter_id):
    logger.api(f"shelter_id: {shelter_id}")
    try:
        token = info.context.headers['authorization']
        assert_capability(token, shelter_id, Cap.READ)
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


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_kpi_history_resolver(obj, info, shelter_id, days=30):
    logger.api(f"shelter_id: {shelter_id} days: {days}")
    try:
        token = info.context.headers['authorization']
        assert_capability(token, shelter_id, Cap.READ)
        items = dashboard_domain.get_kpi_history(shelter_id, days)
        payload = {"success": True, "items": items}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "items": [],
        }
    return payload
