import json
from utils.logger import logger

f= open ("translations.json")
transslations = json.load(f)


def get_translations():
    logger.domain('get translations')
    return transslations