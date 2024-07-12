import json
from utils.logger import logger


def get_translations():
    logger.domain('get translations')
    with open("translations.json") as f:
        translations = json.load(f)
    return translations

def save_translations(data):
    logger.domain('save translations')
    with open("translations.json", 'w') as f:
        json.dump(data, f, indent=4) 