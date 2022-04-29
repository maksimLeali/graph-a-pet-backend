from ariadne import ObjectType
from domain.users import get_first_name


user = ObjectType("User")
user.set_field("first_name", get_first_name)
