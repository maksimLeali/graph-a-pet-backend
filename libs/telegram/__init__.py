from email.message import Message
from telepot.loop import MessageLoop
from telepot import Bot, glance, flavor
from config import cfg
from libs.logger import logger, stringify
import time

def handle(msg):
    logger.info(msg)


TOKEN = cfg['telegram']['token']  # get token from command-line
ADMIN_ID = cfg['telegram']['admin_id']
bot = Bot(TOKEN)

def send_message_to_admin(msg):
    bot.sendMessage(chat_id=ADMIN_ID, text=msg)


