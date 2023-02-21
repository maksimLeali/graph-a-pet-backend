from ariadne import convert_kwargs_to_snake_case
from domain.reports import create_report, update_report, add_reporter
from utils import get_request_user
from utils.logger import logger, stringify
from api.errors import format_error


@convert_kwargs_to_snake_case
def create_report_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token =  info.context.headers.get('authorization')
        user = None
        if token :
            user = get_request_user(token)
        report = create_report(data, user['id'] if user != None else None)
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
    except Exception as e:  
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload

@convert_kwargs_to_snake_case
def respond_to_report_resolver(obj, info, id, reporter): 
    logger.api(
        f"id: {id}\n"\
        f"reporter: {stringify(reporter)}"
    )
    try: 
        token =  info.context.headers.get('authorization')
        user = None
        if token :
            user = get_request_user(token)
        report = add_reporter(id, reporter,  user['id'] if user != None else None)
        payload = {
            "success": True,
            "report": report
        }
    except Exception as e: 
        logger.error(e)
        payload = {
            "success": False,
            "errors": format_error(e)
        }
    return payload