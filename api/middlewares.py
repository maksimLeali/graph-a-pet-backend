"""Authentication middleware.

Authorization lives in AuthorizationService (domain.authorization) and the
GraphQL decorators in api.authorization.decorators — the legacy min_role /
min_shelter_role / assert_shelter_role hierarchy has been removed.
"""
from typing import Any

from graphql import GraphQLError, GraphQLResolveInfo
from api.errors import AuthenticationError, format_error
from domain.users import get_user, update_user_activity
from utils.logger import logger
from config import cfg
import jwt


def auth_middleware(f):
    def function_wrapper(obj: Any, info: GraphQLResolveInfo, **args):
        logger.middleware("check if user is authorized")
        try:
            try:
                bearer = info.context.headers['authorization'].split('Bearer ')[1]
                decoded_bearer = jwt.decode(bearer, cfg['jwt']['secret'], algorithms=["HS256"])
                logger.info(decoded_bearer)

                get_user(decoded_bearer['user']['id'])
            except jwt.ExpiredSignatureError:
                logger.error("Token expired")
                raise AuthenticationError("Token expired")
            except Exception as e:
                logger.error(e)
                raise AuthenticationError('unauthorized')

            update_user_activity(decoded_bearer.get('user').get('id'))
            return f(obj, info, **args)
        except Exception as e:
            error = format_error(e, info.context.headers['authorization'])
            raise GraphQLError(message=error.get('message'), extensions=error)
    return function_wrapper
