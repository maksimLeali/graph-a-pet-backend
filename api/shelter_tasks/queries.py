from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_tasks as shelter_tasks_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission, authorize_from_token
from domain.authorization.catalog import ShelterPermissions
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_tasks_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        tasks, pagination = shelter_tasks_domain.get_paginated_shelter_tasks(common_search)
        payload = {
            "success": True,
            "items": tasks,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@require_permission(ShelterPermissions.TASKS_READ, shelter_argument="shelter_id")
def list_operational_shelter_tasks_resolver(obj, info, shelter_id):
    logger.api(f"shelter_id: {shelter_id}")
    try:
        tasks, pagination = shelter_tasks_domain.get_operational_tasks(shelter_id)
        payload = {"success": True, "items": tasks, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
def get_shelter_task_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        task = shelter_tasks_domain.get_shelter_task(id)
        authorize_from_token(
            info.context.headers['authorization'],
            ShelterPermissions.TASKS_READ,
            task["shelter_id"],
        )
        payload = {
            "success": True,
            "shelter_task": task,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "shelter_task": None,
        }
    return payload
