from domain.donations.donations import expire_stale_pending_donations
from utils.cron import ee
from utils.logger import logger


@ee.on('cron:minutely')
def sweep_stale_pending_donations():
    try:
        count = expire_stale_pending_donations()
        if count:
            logger.info(f'expired {count} stale pending donation(s)')
    except Exception as e:
        logger.error(e)
