from apscheduler.schedulers.background import BackgroundScheduler
from libs.logger import logger
from pyee import EventEmitter
ee = EventEmitter()


def daily():
    logger.info('test')
    ee.emit('cron:daily')
def minutely():
    ee.emit('cron:minutely')

def hourly():
    ee.emit('cron:hourly')

def test():
    ee.emit('cron:test')
    



def start_scheduler (): 
    logger.start('starting scheduler')
    scheduler = BackgroundScheduler()
    
    # scheduler.add_job(daily, 'cron', hour=2)
    scheduler.add_job(daily, 'interval',seconds=5)
    # scheduler.add_job(daily, '', seconds=5)
    scheduler.start()