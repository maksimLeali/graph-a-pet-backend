from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_occupancies as occupancies_domain
import domain.shelter_pets as shelter_pets_domain
from api.errors import format_error, NotFoundError
from api.middlewares import auth_middleware, assert_shelter_role
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_box_occupancies_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        items, pagination = occupancies_domain.get_paginated_occupancies(common_search)
        payload = {"success": True, "items": items, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_current_box_for_pet_resolver(obj, info, shelter_pet_id):
    logger.api(f"shelter_pet_id: {shelter_pet_id}")
    try:
        token = info.context.headers['authorization']
        sp = shelter_pets_domain.get_shelter_pet(shelter_pet_id)
        if sp is None:
            raise NotFoundError(f"no shelter_pet found with id {shelter_pet_id}")
        assert_shelter_role(token, sp["shelter_id"], "STAFF")
        box = occupancies_domain.get_current_box_for_pet(shelter_pet_id)
        payload = {"success": True, "box": box}
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
            "box": None,
        }
    return payload
