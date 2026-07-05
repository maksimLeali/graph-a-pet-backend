from ariadne import convert_kwargs_to_snake_case
from domain.treatments import create_treatment, update_treatment, delete_treatment
from utils.logger import logger, stringify
from utils import get_request_user
from api.errors import format_error
from api.middlewares import auth_middleware


@convert_kwargs_to_snake_case
def create_treatment_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        treatment = create_treatment(data)
        payload = {
            "success": True,
            "treatment": treatment
        }
        logger.check(f"treatment: {stringify(treatment)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
def update_treatment_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        treatment = update_treatment(id, data)
        payload = {
            "success": True,
            "treatment": treatment
        }
        logger.check(f"data: {stringify(data)}")
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": format_error(e, info.context.headers['authorization'])
        }
    return payload

@convert_kwargs_to_snake_case
@auth_middleware
def delete_treatment_resolver(obj, info, id):
    logger.api(f"id: {id}  remove")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        memoriae_id = delete_treatment(id, current_user['id'])
        payload = {
            "success": True,
            "id": memoriae_id
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload
