from domain.shelter_tasks import materialize_recurring_tasks
from utils.cron import ee
from utils.telegram import send_message_to_admin
from utils.logger import logger


@ee.on('cron:daily')
def materialize_shelter_tasks():
    """Ogni giorno materializza le occorrenze delle task ricorrenti per oggi."""
    try:
        created = materialize_recurring_tasks()
        if created:
            send_message_to_admin(
                f"Materialized {created} recurring shelter task(s) for today"
            )
    except Exception as e:
        logger.error(e)
