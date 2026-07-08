from domain.shelter_dashboard import snapshot_all_shelters
from utils.cron import ee
from utils.telegram import send_message_to_admin
from utils.logger import logger


@ee.on('cron:daily')
def snapshot_shelter_kpis():
    """Ogni giorno storicizza i KPI operativi di tutti gli shelter."""
    try:
        saved = snapshot_all_shelters()
        if saved:
            send_message_to_admin(f"Saved {saved} shelter KPI snapshot(s)")
    except Exception as e:
        logger.error(e)
