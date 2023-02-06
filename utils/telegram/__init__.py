from email.message import Message
from telepot.loop import MessageLoop
from telepot import Bot, glance, flavor
from config import cfg
from utils.logger import logger, stringify
import time

def send_message_to_admin(msg):
    SERVICE_IS_ACTIVE = cfg['telegram']['active']
    if SERVICE_IS_ACTIVE :
        TOKEN = cfg['telegram']['token']
        ADMIN_ID = cfg['telegram']['admin_id']
        bot = Bot(TOKEN)
        bot.sendMessage(chat_id=ADMIN_ID, text=msg)
        return
    logger.warning('Notifications via telegram disabled')
    
    