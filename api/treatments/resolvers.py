from ariadne import ObjectType

import domain.treatments as treatments_domain
from utils.logger import logger, stringify

treatment = ObjectType('Treatment')

@treatment.field('health_card')
def health_card_resolver(obj, info): 
    try: 
        health_card = treatments_domain.get_health_card(obj['health_card_id'])
        resolved = health_card
        logger.check(f"health_card: {stringify(health_card)}")
    except Exception as e:
        logger.error(e)
        resolved= None
    return resolved

@treatment.field('booster')
def booster_resolver(obj, info):
    try: 
        booster = treatments_domain.get_treatment(obj['booster_id'])
        resolved = booster
        logger.check(f"health_card: {stringify(booster)}")
    except Exception as e:
        logger.error(e)
        resolved= None
    return resolved
    