import data.ownerships as ownerships_data

def get_owenrship_user():
    return "ok"

def create_ownership(data):
    return ownerships_data.create_ownership(data)

def update_ownership(id, data):
    return ownerships_data.update_ownership(id, data)

def get_ownerships():
    return ownerships_data.get_ownerships()

def get_ownership(id): 
    return ownerships_data.get_ownership(id)