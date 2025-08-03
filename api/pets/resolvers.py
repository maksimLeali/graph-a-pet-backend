from ariadne import ObjectType, convert_kwargs_to_snake_case

import domain.pets as pets_domain
import domain.reports as reports_domain
import domain.health_cards as health_cards_domain
from utils.logger import logger, stringify
from api.errors import error_pagination
from utils import format_common_search
from datetime import datetime

pet = ObjectType("Pet")



def years_from_now(date_str):
    input_date = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    years_passed = today.year - input_date.year

    # Adjust if the anniversary hasn't occurred yet this year
    if (today.month, today.day) < (input_date.month, input_date.day):
        years_passed -= 1

    return years_passed


@pet.field('years')
def resolve_profile_picture(obj,info):
    return years_from_now(obj.get('birthday'))

@pet.field('main_picture')
def resolve_profile_picture(obj,info):
    logger.api(f'{obj["id"]}')
    try :
        media = pets_domain.get_main_pic(obj['id'])
        return media
    except Exception as e:
        logger.error(e)
        

@pet.field('pictures')
@convert_kwargs_to_snake_case
def resolve_pictures(obj,info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['and']={
         **(common_search['filters'].get('and') if common_search.get('filters').get('and')!= None else {}), 
         **{
            "fixed": {
                **(common_search['filters'].get('and').get('fixed') if common_search.get('filters').get('and')!= None and common_search['filters'].get('and').get('fixed') != None else {}),
                **{
                    "scope": "pet_picture",
                    "ref_id": obj["id"]
                }
            }
         }
    }
    logger.api(
        f"pet_id: {obj['id']}\n"\
        f'common_search: {stringify(common_search)}'
    )
    try: 
        pictures, pagination = pets_domain.get_pictures(common_search)
        resolved = {
            "items": pictures,
            "pagination": pagination,
            "success": True
        }
        logger.check(
            f"pictures: {len(pictures)}\n"\
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


@pet.field('ownerships')
@convert_kwargs_to_snake_case
def pet_ownerships_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['and']= { 
        **(common_search['filters'].get('and') if common_search.get('filters').get('and')!= None else {}), 
        **{ 
            'fixed': {
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
    
@pet.field('report')
@convert_kwargs_to_snake_case
def pet_report_resolver(obj, info):
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
        reports, pagination= reports_domain.get_paginated_reports(common_search)
        return reports[0]
    except Exception as e:
        logger.error(e)
        return None
