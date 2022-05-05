from ariadne import ObjectType
from domain.coats import  get_pet


coat = ObjectType("Coat")
coat.set_field("pet", get_pet)