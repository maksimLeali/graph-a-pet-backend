from ariadne import ObjectType, convert_kwargs_to_snake_case

import domain.pets as pets_domain
import domain.health_cards as health_cards_domain
from utils.logger import logger, stringify
from api.errors import error_pagination
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
    
    logger.api(
        f"pet_id: {obj['id']}\n"\
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


@pet.field('health_card')
@convert_kwargs_to_snake_case
def pet_health_card_resolver(obj, info):
    try:
        common_search = {
            "pagination":{"page_size" : 20, "page": 0},
            "ordering": {"order_by": "created_at", "order_direction": "ASC"},
            "filters" : {
                "and" : {
                    "fixed": {
                        "pet_id" : obj['id']
                    }
                }
            }
        } 
        health_cards, pagination= health_cards_domain.get_paginated_health_cards(common_search)
        return health_cards[0]
    except Exception as e :
        logger.error(e)
        return None