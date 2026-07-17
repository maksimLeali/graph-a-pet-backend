from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_claim_requests as claims_domain
from api.errors import format_error, error_pagination
from api.middlewares import auth_middleware
from api.authorization.decorators import authorize_from_token, require_permission
from domain.authorization.catalog import ShelterPermissions, PlatformPermissions
from utils import get_request_user, format_common_search
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def list_my_shelter_claim_requests_resolver(obj, info: GraphQLResolveInfo, search=None):
    logger.api(f"search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        common_search = format_common_search(search or {})
        items, pagination = claims_domain.list_my_claims(current_user.get("id"), common_search)
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
def list_shelter_claim_requests_resolver(obj, info: GraphQLResolveInfo, shelter_id, search=None):
    logger.api(f"shelter_id: {shelter_id} search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        authorize_from_token(token, ShelterPermissions.OWNERSHIP_TRANSFER, shelter_id=shelter_id)
        common_search = format_common_search(search or {})
        items, pagination = claims_domain.list_shelter_claims(shelter_id, common_search)
        payload = {"success": True, "items": items, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CLAIMS_REVIEW, platform=True)
def list_platform_shelter_claim_requests_resolver(obj, info: GraphQLResolveInfo, search=None):
    """Back-office review queue: every claim request across all shelters."""
    logger.api(f"search: {stringify(search)}")
    try:
        common_search = format_common_search(search or {})
        items, pagination = claims_domain.list_platform_claims(common_search)
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
