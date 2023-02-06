from ariadne import ObjectType, convert_kwargs_to_snake_case

import domain.pets as pets_domain
from utils.logger import logger, stringify
from controller.errors import error_pagination
from utils import format_common_search

pet = ObjectType("Pet")

@pet.field('ownerships')
@convert_kwargs_to_snake_case
def pet_ownerships_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['and']= { 
        **(common_search['filters'].get('and') if common_search.get('filters').get('and')!= None else {}), 
        **{ 
            'fixed' :  {
                **(common_search['filters'].get('and').get('fixed') if common_search.get('filters').get('and')!= None and common_search['filters'].get('and').get('fixed') != None else {}),
                **{'pet_id' : obj['id'] }
            } 
        } 
    }
    logger.controller(
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
            f"ownerships: {len(ownerships)}\n"\
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


pet.set_field("body", pets_domain.get_body)