from domain.notifications import (
    generate_treatment_reminders,
    generate_pet_birthdays,
)
from utils.cron import ee
from utils.telegram import send_message_to_admin
from utils.logger import logger


@ee.on('cron:daily')
def generate_daily_notifications():
    """Every day generate treatment reminders (vaccines / operations /
    antiparasitics due today) and pet birthday notifications. Both are
    idempotent through dedupe_key, so re-runs never duplicate."""
    try:
        reminders = generate_treatment_reminders()
        birthdays = generate_pet_birthdays()
        if reminders or birthdays:
            send_message_to_admin(
                f"Generated {reminders} treatment reminder(s) and "
                f"{birthdays} birthday notification(s) for today"
            )
    except Exception as e:
        logger.error(e)
