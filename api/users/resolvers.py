from ariadne import ObjectType, convert_kwargs_to_snake_case
import domain.users as users_domain
from libs.logger import logger, stringify
from libs.utils import format_common_search
from api.errors import error_pagination, format_error

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
    logger.api(
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
