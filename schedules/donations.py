from domain.donations.donations import expire_stale_pending_donations
from domain.donations.funding_needs import reset_recurring_funding_needs
from utils.cron import ee
from utils.dates import utc_now
from utils.logger import logger


@ee.on('cron:minutely')
def sweep_stale_pending_donations():
    try:
        count = expire_stale_pending_donations()
        if count:
            logger.info(f'expired {count} stale pending donation(s)')
    except Exception as e:
        logger.error(e)


@ee.on('cron:daily')
def reset_monthly_funding_need_goals():
    """Monthly goal reset ("traguardi"): on the 1st of the month every
    ACTIVE recurring funding need restarts from zero. Runs at the daily
    cron time (02:00 Europe/Berlin, see utils/cron) — goal periods are NOT
    shelter-timezone-aware, unlike the legacy pet limit's period bounds."""
    try:
        if utc_now().day != 1:
            return
        count = reset_recurring_funding_needs()
        logger.info(f'monthly goal reset: {count} recurring funding need(s) zeroed')
    except Exception as e:
        logger.error(e)
