from ariadne import convert_kwargs_to_snake_case
from domain.reports import create_report, update_report
from utils.logger import logger, stringify
from api.errors import format_error


@convert_kwargs_to_snake_case
def create_report_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        report = create_report(data)
        payload = {
            "success": True,
            "report": report
        }
        logger.check(f"report: {stringify(report)}")
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload

@convert_kwargs_to_snake_case
def update_report_resolver(obj, info, id, data):
    logger.api(
        f"id: {id}\n"\
        f"data: {stringify(data)}"
    )
    try:
        report = update_report(id, data)
        payload = {
            "success": True,
            "report": report
        }
        logger.check(f"data: {stringify(data)}")
    except Exception as e:  # todo not found
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload
