from ariadne import convert_kwargs_to_snake_case
from domain.treatments import create_treatment, update_treatment
from utils.logger import logger, stringify
from api.errors import format_error


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
