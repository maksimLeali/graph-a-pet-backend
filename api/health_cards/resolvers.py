from ariadne import ObjectType
from domain.health_cards import  get_pet


health_card = ObjectType("HealthCard")
health_card.set_field("pet", get_pet)