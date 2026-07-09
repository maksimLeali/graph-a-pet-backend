from ariadne import convert_kwargs_to_snake_case
from graphql import GraphQLError, GraphQLResolveInfo
import domain.shelter_people as people_domain
from api.errors import format_error
from api.middlewares import auth_middleware, assert_shelter_role
from utils import format_common_search
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def list_shelter_people_resolver(obj, info: GraphQLResolveInfo, shelter_id, search=None):
    logger.api(f"shelter_id: {shelter_id} search: {stringify(search)}")
    try:
        token = info.context.headers['authorization']
        assert_shelter_role(token, shelter_id, "STAFF")
        common_search = format_common_search(search or {})
        people, pagination = people_domain.get_paginated_shelter_people(shelter_id, common_search)
        payload = {"success": True, "items": people, "pagination": pagination}
    except Exception as e:
        logger.error(e)
        error = format_error(e, info.context.headers['authorization'])
        raise GraphQLError(error.get('message'), extensions=error)
    return payload


@convert_kwargs_to_snake_case
@auth_middleware
def get_shelter_person_resolver(obj, info, id):
    logger.api(f"id: {id}")
    try:
        token = info.context.headers['authorization']
        person = people_domain.get_shelter_person(id)
        assert_shelter_role(token, person["shelter_id"], "STAFF")
        return person
    except Exception as e:
        logger.error(e)
        return None
