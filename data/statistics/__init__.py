from sqlalchemy import select, text
from api.errors import BadRequest, NotFoundError
from data.query_builder import build_count, build_query
from libs.logger import logger, stringify
from datetime import datetime
from .models import Statistic
from data import db
from sqlalchemy.exc import InvalidRequestError
import uuid


def create_statistic(data):
    logger.data(f"data: {stringify(data)}")
    try:
        statistic_model = Statistic(
            id=f"{uuid.uuid4()}",
            date=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            all_users=data.get('all_users'),
            all_pets=data.get('all_pets'),
            active_users=data.get('active_users'),
        )
        db.session.add(statistic_model)
        db.session.commit()
        statistic = statistic_model.to_dict()
        logger.check(f"statistic: {stringify(statistic)}")
        return statistic
    except Exception as e:
        logger.error(e)
        raise e


def update_statistic(id, data):
    logger.data(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        statistic_model = db.session.query(
            Statistic).filter(Statistic.id == id)
        if not statistic_model:
            raise NotFoundError(f"no statistic found with id: {id}")
        statistic_old = statistic_model.first().to_dict()
        statistic_model.update(data)
        db.session.commit()
        statistic = {**statistic_old, **statistic_model.first().to_dict()}
        logger.check(f'statistic: {stringify(statistic)}')
        return statistic
    except InvalidRequestError as e:
        logger.error(e)
        raise BadRequest(e)
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="users", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except Exception as e:
        logger.error(e)
        raise e


def get_statistics(common_search):
    logger.data(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="statistics", ordering=common_search.get("ordering"),
                            filters=common_search.get('filters'), pagination=common_search.get('pagination'))
        manager = select(Statistic).from_statement(text(query))
        statistics = db.session.execute(manager).scalars()
        return [statistic.to_dict() for statistic in statistics]
    except Exception as e:
        logger.error(e)
        raise e


def get_dashboard():
    logger.data("getting dashboard")
    try:
        query = "SELECT "\
            "date_trunc('day', stats.date) AS day, "\
            "AVG(stats.active_users) AS active_users, "\
            "AVG(stats.all_users) AS all_users, "\
            "AVG(stats.all_pets) AS all_pets "\
                "FROM "\
            "statistics stats "\
                "GROUP BY "\
            "day "\
                "ORDER BY "\
            "day DESC "\
            "LIMIT 30"
        manager = select(Statistic).from_statement(text(query))
        statistics = db.session.execute(manager).scalar()
        return [statistics.to_dict() for statistic in statistics]
    except Exception as e:
        logger.error(e)
        raise e
