from apscheduler.schedulers.background import BackgroundScheduler
from libs.logger import logger
from pyee import EventEmitter
ee = EventEmitter()


def daily():
    ee.emit('cron:daily')

def hourly():
    ee.emit('cron:hourly')

def minutely():
    ee.emit('cron:minutely')
    
def test():
    ee.emit('cron:test')
    



def start_scheduler (): 
    logger.start('starting scheduler')
    scheduler = BackgroundScheduler()
    
    # setting scheduler's interval
    scheduler.add_job(daily, 'cron', hour=2)
    scheduler.add_job(hourly, 'interval', hours=1)
    scheduler.add_job(minutely, 'interval', minutes=1 )
    # scheduler.add_job(test, 'interval', seconds=10)
    
    # starting scheduler
    scheduler.start()