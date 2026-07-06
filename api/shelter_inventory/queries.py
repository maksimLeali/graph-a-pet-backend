from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_inventory as inventory_domain
from api.errors import format_error
from api.middlewares import auth_middleware, assert_shelter_role
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_inventory_items_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        items, pagination = inventory_domain.get_paginated_items(common_search)
        payload = {"success": True, "items": items, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_inventory_item_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        item = inventory_domain.get_shelter_inventory_item(id)
        payload = {"success": True, "item": item}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "item": None,
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_inventory_movements_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        movements, pagination = inventory_domain.get_paginated_movements(common_search)
        payload = {"success": True, "items": movements, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def list_low_stock_items_resolver(obj, info, shelter_id):
    logger.api(f"shelter_id: {shelter_id}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_id, "STAFF")
        items, pagination = inventory_domain.list_low_stock_items(shelter_id)
        payload = {"success": True, "items": items, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload
