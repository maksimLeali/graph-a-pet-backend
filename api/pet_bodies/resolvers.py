from ariadne import ObjectType
from domain.pet_bodies import  get_pet, get_coat


pet_body = ObjectType("PetBody")
pet_body.set_field("coat", get_coat)