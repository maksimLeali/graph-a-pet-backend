from ariadne import ObjectType
from domain.users import  get_user_ownerships


user = ObjectType("User")
user.set_field("ownerships", get_user_ownerships)