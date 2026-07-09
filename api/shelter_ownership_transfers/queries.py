from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_ownership_transfers as transfers_domain
from api.errors import format_error, error_pagination
from api.middlewares import auth_middleware, assert_shelter_role
from utils import get_request_user, format_common_search
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def list_my_ownership_transfers_resolver(obj, info: GraphQLResolveInfo, search=None):
    logger.api(f"search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        common_search = format_common_search(search or {})
        items, pagination = transfers_domain.list_my_transfers(current_user.get("id"), common_search)
        payload = {"success": True, "items": items, "pagination": pagination}
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
def list_shelter_ownership_transfers_resolver(obj, info: GraphQLResolveInfo, shelter_id, search=None):
    logger.api(f"shelter_id: {shelter_id} search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_id, "OWNER")
        common_search = format_common_search(search or {})
        items, pagination = transfers_domain.list_shelter_transfers(shelter_id, common_search)
        payload = {"success": True, "items": items, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload
