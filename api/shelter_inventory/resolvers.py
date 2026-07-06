from ariadne import ObjectType
from domain.shelter_inventory import (
    get_shelter,
    get_current_quantity,
    get_is_below_threshold,
    get_item_movements,
    get_item,
    get_registered_by,
)

shelter_inventory_item = ObjectType("ShelterInventoryItem")
shelter_inventory_item.set_field("shelter", get_shelter)
shelter_inventory_item.set_field("current_quantity", get_current_quantity)
shelter_inventory_item.set_field("is_below_threshold", get_is_below_threshold)
shelter_inventory_item.set_field("movements", get_item_movements)

shelter_inventory_movement = ObjectType("ShelterInventoryMovement")
shelter_inventory_movement.set_field("item", get_item)
shelter_inventory_movement.set_field("registered_by", get_registered_by)
