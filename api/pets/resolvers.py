from ariadne import ObjectType, convert_kwargs_to_snake_case

import domain.pets as pets_domain
from libs.logger import logger, stringify
from api.errors import error_pagination
from libs.utils import format_common_search


@convert_kwargs_to_snake_case
def pet_ownerships_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['fixeds']['user_id'] = obj['id']
    logger.api(
        f"user_id: {obj['id']}\n"\
        f'common_search: {stringify(common_search)}'
    )
    try: 
        ownerships, pagination= pets_domain.get_ownerships(common_search)
        resolved = {
            "items": ownerships,
            "pagination": pagination,
            "success": True
        }
        logger.check(
            f"ownerships: {stringify(ownerships)}\n"\
            f"pagination: {stringify(pagination)}"
        )
    except Exception as  e: 
        logger.error(e)
        resolved= {
            "items": [],
            "pagination": error_pagination,
            "success": False,
            "errors":[str(e)] 
        }
    return resolved

pet = ObjectType("Pet")
pet.set_field("ownerships", pet_ownerships_resolver)
pet.set_field("body", pets_domain.get_body)