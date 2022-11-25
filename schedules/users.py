from data.pets import get_all_pets
from libs.cron import ee
from data.users import get_all_active_users, get_all_users
from libs.logger import logger, stringify
from data.statistics import create_statistic

@ee.on('cron:daily')
def save_daily_users_activity():
    try: 
        data =  {
            "active_per_day" :  len(get_all_active_users()),
            "all_users" :   len(get_all_users()),
            "all_pets" :   len(get_all_pets())
        }
        create_statistic(data)  
    except Exception as e :
        logger.error(e)