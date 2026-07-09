from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelters as shelters_domain
from api.errors import format_error, error_pagination
from api.middlewares import auth_middleware
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelters_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        shelters, pagination = shelters_domain.get_paginated_shelters(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        payload = {
            "success": True,
            "items": shelters,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        shelter = shelters_domain.get_shelter(id)
        payload = {
            "success": True,
            "shelter": shelter,
        }
        logger.check(f"shelter: {stringify(shelter)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "shelter": None,
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def discover_shelters_resolver(obj, info: GraphQLResolveInfo, search=None):
    logger.api(f"search: {stringify(search)}")
    try:
        items, pagination = shelters_domain.discover_shelters(search)
        payload = {
            "success": True,
            "items": items,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "items": [],
            "pagination": error_pagination,
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_public_shelter_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        return shelters_domain.get_public_shelter(id)
    except Exception as e:
        logger.error(e)
        return None
