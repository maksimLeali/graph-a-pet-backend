
from domain.statistics import get_real_time_statistic
from utils.cron import ee
from utils.logger import logger, stringify
from repository.statistics import create_statistic

@ee.on('cron:hourly')
def save_daily_users_activity():
    try: 
        data = get_real_time_statistic()
        create_statistic(data)  
    except Exception as e :
        logger.error(e)