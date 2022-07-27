from ariadne import ObjectType, convert_kwargs_to_snake_case
from domain.health_cards import  get_pet
from libs.logger import logger, stringify
from libs.utils import format_common_search
from api.errors import error_pagination, format_error
import domain.health_cards as health_cards_domain


health_card = ObjectType("HealthCard")
health_card.set_field("pet", get_pet)

@health_card.field("treatments")
@convert_kwargs_to_snake_case
def health_card_treatments_resolver(obj, info, common_search):
    logger.info(common_search)
    common_search= format_common_search(common_search)
    common_search['filters']['fixed']['health_card_id'] = obj['id']
    logger.api(
        f"health_card_id: {obj['id']}\n"\
        f'common_search: {stringify(common_search)}'
    )
    try: 
        treatments, pagination= health_cards_domain.get_treatments(common_search)
        resolved = {
            "items": treatments,
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
