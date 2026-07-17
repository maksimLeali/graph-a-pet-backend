from ariadne import convert_kwargs_to_snake_case
import domain.walk_ratings as walk_ratings_domain
from utils.logger import logger, stringify
from utils import format_common_search, get_request_user
from api.errors import error_pagination, format_error
from api.middlewares import auth_middleware


# custody levels that grant a user access to a pet's data
_ALLOWED_CUSTODY = ["OWNER", "SUB_OWNER", "PET_SITTER"]


def _scope_to_user(common_search, user_id):
    """Force the walk_ratings query to only the pets the user has custody of.
    Injects the join path walk_ratings -> walks -> treatments -> health_cards
    -> pets -> ownerships and constrains ownerships.user_id server-side, so a
    client cannot widen the scope by omitting or altering the filters."""
    def branch(node, table):
        return node.setdefault('and', {}).setdefault('join', {}).setdefault(table, {})

    filters = common_search.setdefault('filters', {})
    node = branch(filters, 'walks')
    node = branch(node, 'treatments')
    node = branch(node, 'health_cards')
    node = branch(node, 'pets')
    ownerships = branch(node, 'ownerships').setdefault('and', {})
    ownerships.setdefault('fixed', {})['user_id'] = user_id
    ownerships.setdefault('lists', {})['custody_level'] = _ALLOWED_CUSTODY
    return common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_walk_ratings_resolver(obj, info, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    try:
        token = info.context.headers['authorization']
        current_user = get_request_user(token)
        common_search = format_common_search(common_search)
        common_search = _scope_to_user(common_search, current_user['id'])
        walk_ratings, pagination = walk_ratings_domain.get_paginated_walk_ratings(common_search)
        payload = {
            "success": True,
            "items": walk_ratings,
            "pagination": pagination,
        }
        logger.check(f"walk_ratings found: {len(walk_ratings)}")
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "items": [],
            "pagination": error_pagination
        }
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_walk_rating_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        walk_rating = walk_ratings_domain.get_walk_rating(id)
        payload = {
            "success": True,
            "walk_rating": walk_rating
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "walk_rating": None,
            "error": format_error(e, info.context.headers['authorization'])
        }
    return payload
