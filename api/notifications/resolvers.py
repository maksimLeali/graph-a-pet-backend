from ariadne import ObjectType

# Notifications expose flat scalar fields (+ JSON payload); nested lookups are
# resolved lazily by the client through the entity pointers (pet_id, shelter_id,
# actor_user_id, ...). Kept for parity with the other modules and future fields.
notification = ObjectType("Notification")
