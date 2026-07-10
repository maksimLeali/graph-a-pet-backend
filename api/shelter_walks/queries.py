from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_walks as shelter_walks_domain
from api.errors import format_error
from api.middlewares import auth_middleware, assert_shelter_role
from api.permissions import assert_capability, Cap
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_walks_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        walks, pagination = shelter_walks_domain.get_paginated_shelter_walks(common_search)
        payload = {"success": True, "items": walks, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_walk_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        walk = shelter_walks_domain.get_shelter_walk(id)
        payload = {"success": True, "shelter_walk": walk}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "shelter_walk": None,
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def list_operational_shelter_walks_resolver(obj, info, shelter_id):
    logger.api(f"shelter_id: {shelter_id}")
    try:
        token = info.context.headers['authorization']
        assert_capability(token, shelter_id, Cap.READ)
        walks, pagination = shelter_walks_domain.get_operational_walks(shelter_id)
        payload = {"success": True, "items": walks, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def list_pets_needing_walk_resolver(obj, info, shelter_id, hours=24):
    logger.api(f"shelter_id: {shelter_id} hours: {hours}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_id, "STAFF")
        pets, pagination = shelter_walks_domain.get_pets_needing_walk(shelter_id, hours)
        payload = {"success": True, "items": pets, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload
