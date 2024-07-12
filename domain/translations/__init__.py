import json
from utils.logger import logger


def get_translations():
    logger.domain('get translations')
    with open("translations.json") as f:
        translations = json.load(f)
    return translations


def get_app_translations():
    logger.domain('get app translations')
    with open("translations.json") as f:
        translations = json.load(f)
    extracted = {}
    
     # Iterate over each language
    for lang, content in translations.items():
    
        # If 'breeds' exists in the current language root, move it
        if 'breeds' in content:
            breeds = content.pop('breeds')
            content['graph_a_pet_app']['pets']['breeds'] = breeds
    
        # Extract the 'graph_a_pet_app' key for the current language
        extracted[lang] = {
            "graph_a_pet_app": content['graph_a_pet_app']
        }
    return extracted

def save_translations(data):
    logger.domain('save translations')
    with open("translations.json", 'w') as f:
        json.dump(data, f, indent=4) 