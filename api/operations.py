from ariadne import ObjectType
from api.users.queries import *
from api.users.mutations import *
from api.users.resolvers import user


query = ObjectType("Query")
query.set_field("listUsers", list_users_resolver)
query.set_field("getUser", get_user_resolver)

mutation = ObjectType("Mutation")
mutation.set_field('createUser', create_user_resolver)
mutation.set_field('updateUser', update_user_resolver)

object_types = [query, mutation, user]