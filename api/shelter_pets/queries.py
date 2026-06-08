from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_pets as shelter_pets_domain
from api.errors import format_error
from api.middlewares import auth_middleware
from utils.logger import logger, stringify
from utils import format_common_search


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_pets_resolver(obj, info: GraphQLResolveInfo, common_search):
    logger.api(f"common_search: {stringify(common_search)}")
    common_search = format_common_search(common_search)
    try:
        shelter_pets, pagination = shelter_pets_domain.get_paginated_shelter_pets(common_search)
        payload = {
            "success": True,
            "items": shelter_pets,
            "pagination": pagination,
        }
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_pet_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        shelter_pet = shelter_pets_domain.get_shelter_pet(id)
        payload = {
            "success": True,
            "shelter_pet": shelter_pet,
        }
    except Exception as e:
        logger.error(e)
        payload = {
            "success": False,
            "shelter_pet": None,
            "error": format_error(e, info.context.headers['authorization']),
        }
    return payload
