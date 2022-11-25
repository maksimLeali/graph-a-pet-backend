from apscheduler.schedulers.background import BackgroundScheduler
from libs.logger import logger
from pyee import EventEmitter
from config import cfg

ee = EventEmitter()


def daily():
    ee.emit('cron:daily')

def hourly():
    ee.emit('cron:hourly')

def minutely():
    logger.critical('minutes')
    ee.emit('cron:minutely')
    
def test():
    ee.emit('cron:test')
    

def start_scheduler (): 
    logger.setup('starting scheduler')
    scheduler = BackgroundScheduler(timezone="Europe/Berlin")
    
    # setting scheduler's interval
    scheduler.add_job(daily, 'cron', hour=2)
    scheduler.add_job(hourly, 'interval', hours=1)
    scheduler.add_job(minutely, 'interval', minutes=1 )
    if(cfg['cron']['test_enabled']):
        logger.setup('test cron enabled')
        scheduler.add_job(test, 'interval', seconds=5)
    
    # starting scheduler
    scheduler.start()