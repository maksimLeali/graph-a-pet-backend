
from domain.statistics import get_real_time_statistic
from libs.cron import ee
from libs.logger import logger, stringify
from data.statistics import create_statistic

@ee.on('cron:daily')
def save_daily_users_activity():
    try: 
        data = get_real_time_statistic()
        create_statistic(data)  
    except Exception as e :
        logger.error(e)