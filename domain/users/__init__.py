import data.users as users_data


def get_user_ownerships(obj, info):
    return []

def create_user(data):
    
    return users_data.create_user(data)

def update_user(id, data):
    return users_data.update_user(id, data)

def get_users():
    return users_data.get_users()

def get_user(id): 
    return users_data.get_user(id).to_dict()

def add_dog(user_id, dog):
    return "ok"

def get_user_from_email_password(email, password):
    return users_data.get_user_from_email_password(email, password)