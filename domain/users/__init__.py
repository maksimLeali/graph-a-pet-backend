import data.users as users_data

def get_first_name(obj, info):
    return 'pippo'


def create_user(data):
    
    return users_data.create_user(data)

def update_user(id, data):
    return users_data.update_user(id, data)

def get_users():
    return users_data.get_users()

def get_user(id): 
    return users_data.get_user(id)