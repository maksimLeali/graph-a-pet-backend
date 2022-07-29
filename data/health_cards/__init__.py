import uuid
from datetime import datetime
from data.health_cards.models import HealthCard
from data import db
from api.errors import InternalError, NotFoundError, BadRequest
from libs.logger import logger, stringify
from sqlalchemy.exc import ProgrammingError
from data.query_builder import build_query, build_count
from sqlalchemy import select, text

def create_health_card(data):
    logger.data(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        health_card = HealthCard(
            id = f"{uuid.uuid4()}",
            pet_id = data['pet_id'],
            notes = [],
            treatments = [],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        db.session.add(health_card)
        db.session.commit()
        logger.check(f"health_card: {health_card}")
        return health_card.to_dict()
    except Exception as e:
        logger.error(e)
        raise BadRequest(e)
    
def update_health_card(id, data):
    logger.data(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        health_card_model = db.session.query(HealthCard).filter(HealthCard.id== id)
        if not health_card_model:
            raise NotFoundError(f"no health_card found with id: {id}")
        health_card_old = health_card_model.first().to_dict()
        health_card_model.update(data)
        db.session.commit()
        health_card= {**health_card_old, **health_card_model.first().to_dict()}
        logger.check(f'health_card: {stringify(health_card)}')
        return  health_card
    except Exception as e:
        logger.error(e)
        raise e

def get_health_cards(common_search):
    logger.data(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="health_cards",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        logger.check(f"query: {query}")
        manager = select(HealthCard).from_statement(text(query))
        health_cards_model = db.session.execute(manager).scalars()
        health_cards = [health_card.to_dict() for health_card in health_cards_model]
        logger.check(f"health_cards found {len(health_cards)}")
        return health_cards
    except ProgrammingError as e:
        logger.error(e)
        exception = BadRequest("The fields provided may contains syntax errors")
        exception.extension['extra'] = str(e)
        raise exception
    except Exception as e: 
        logger.error(e)
        raise e

def get_health_card(id):
    logger.data(f"id: {id}")
    try:
        health_card_model = HealthCard.query.get(id)
        if not health_card_model:
            raise  
        health_card = health_card_model.to_dict()
        logger.check(f"health_card: {stringify(health_card)}")
        return health_card
    except Exception as e: 
        logger.error(e)
        raise e

def get_total_items(common_search):
    try:
        query = build_count(table="health_cards",filters= common_search['filters'] )
        result = db.session.execute(query)
        return result.first()[0]
    except ProgrammingError as e: 
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e