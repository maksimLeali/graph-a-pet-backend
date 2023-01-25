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
        query = "SELECT \n"\
                    "\tdate_trunc('day', stats.date) AS c_date, \n"\
                    "\tROUND(AVG(stats.active_users)::NUMERIC, 2) AS active_users, \n"\
                    "\tROUND(AVG(stats.all_users)::NUMERIC, 2) AS all_users, \n"\
                    "\tROUND(AVG(stats.all_pets)::NUMERIC, 2) AS all_pets, \n"\
                    "\tgen_random_uuid() as id \n"\
                "FROM \n"\
                    "\tstatistics stats \n"\
                "WHERE \n"\
                    "\tCASE \n"\
                        "\t\tWHEN date_part('day', now()) < 7 then stats.date > current_date - interval '7' DAY \n"\
                        "\t\telse stats.date >  date_trunc('month', now()) \n"\
                    "\tEND \n"\
                "GROUP BY \n"\
                    "\tc_date \n"\
                "ORDER BY \n"\
                    "\tc_date ASC \n"\
                "LIMIT 30"
        logger.info(query)
        to_return = []
        # manager = select(Statistic).from_statement(text(query))
        statistics = db.engine.execute(query)
        for row in statistics:
            to_return.append({
                "id": row.id,
                "active_users": int(row.active_users),
                "all_users": int(row.all_users),
                "all_pets": int(row.all_pets),
                "date": str(row.c_date)
                })
        return to_return
    except Exception as e:
        logger.error(e)
        raise e
