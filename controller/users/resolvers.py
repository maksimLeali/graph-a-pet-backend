from ariadne import ObjectType, convert_kwargs_to_snake_case
import domain.users as users_domain
from utils.logger import logger, stringify
from utils import format_common_search
from controller.errors import error_pagination, format_error
from repository.ownerships.models import CustodyLevel
user = ObjectType("User")

@user.field("ownerships")
@convert_kwargs_to_snake_case
def user_ownerships_resolver(obj, info, common_search):
    common_search= format_common_search(common_search)
    common_search['filters']['and']= { 
        **(common_search['filters'].get('and') if common_search.get('filters').get('and')!= None else {}), 
        **{ 
            'fixed' :  {
                **(common_search['filters'].get('and').get('fixed') if common_search.get('filters').get('and')!= None and common_search['filters'].get('and').get('fixed') != None else {}),
                **{'user_id' : obj['id'] }
            } 
        } 
    } 
    logger.controller(
        f"user_id: {obj['id']}\n"\
        f'common_search: {stringify(common_search)}'
    )
    try: 
        ownerships, pagination= users_domain.get_ownerships(common_search)
        resolved = {
            "items": ownerships,
            "pagination": pagination,
            "success": True
        }
        logger.check(f"pagination: {stringify(pagination)}")
    except Exception as  e: 
        logger.error(e)
        resolved= {
            "items": [],
            "pagination": error_pagination,
            "success": False,
            "error": format_error(e,info.context.headers['authorization']) 
        }
    return resolved

@user.field('pets_on_loan')
def pets_on_loan_resolver(obj, info ):
    filters = { 
        "pagination": {
            "page_size": 10000,
            "page": 0,
        },  
        "ordering":{
            "order_by":"created_at",
            "order_direction":"desc"
        },

        "filters" : { 
            "and": {
                "lists" : {
                    "custody_level" : [
                        CustodyLevel.SUB_OWNER.name, 
                        CustodyLevel.PET_SITTER.name
                    ]
                },
                "fixed": {
                    "user_id" : obj["id"]
                } 
            }
        }
    }
    try : 
        logger.controller(f"filters : {stringify(filters)}")
        total_items = users_domain.count_ownerships(filters)
        return total_items
    except Exception as e: 
        raise e

@user.field('pets_owned')
def pets_owned_resolver(obj, info ):
    filters = { 
        "pagination": {
            "page_size": 10000,
            "page": 0,
        }, 
        "ordering":{
            "order_by":"created_at",
            "order_direction":"desc"
        },
 
        "filters" : { 
            "and": {
                "fixed": {
                    "custody_level": CustodyLevel.OWNER.name,
                    "user_id" : obj["id"]
                } 
            }
        }
    }
    try : 
        logger.controller(f"filters : {stringify(filters)}")
        total_items = users_domain.count_ownerships(filters)
        return total_items
    except Exception as e: 
        raise e
    
@user.field('profile_picture')
def resolve_profile_picture(obj,info):
    logger.controller(f'{obj["id"]}')
    try :
        media = users_domain.get_profile_pic(obj['id'])
        return media
    except Exception as e:
        logger.error(e)
        