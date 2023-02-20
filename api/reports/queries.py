from ariadne import convert_kwargs_to_snake_case
import domain.reports as reports_domain
from utils.logger import logger, stringify
from utils import format_common_search
from api.errors import InternalError, error_pagination, format_error
from api.middlewares import min_role, RoleLevel


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def list_reports_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        common_search = format_common_search(common_search)
        reports, pagination = reports_domain.get_paginated_reports(common_search)
        payload = {
            "success": True,
            "items": reports,
            "pagination": pagination,
        }
        logger.check(f"reports found: {len(reports)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) ,
            "items": [],
            "pagination": error_pagination 
        }
    return payload


@convert_kwargs_to_snake_case
@min_role(RoleLevel.ADMIN.name)
def get_report_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        report = reports_domain.get_report(id)
        payload = {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "report":None, 
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return payload