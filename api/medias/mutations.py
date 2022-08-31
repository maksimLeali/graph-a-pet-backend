from ariadne import convert_kwargs_to_snake_case
from domain.medias import create_media, update_media

@convert_kwargs_to_snake_case
def update_media_resolver(obj, info, id, data):
    try:
        media = update_media(id, data)
        payload = {
            "success": True,
            "media": media
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
