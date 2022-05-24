from ariadne import ObjectType
from domain.users import  get_ownerships

user = ObjectType("User")
user.set_field("ownerships", get_ownerships)