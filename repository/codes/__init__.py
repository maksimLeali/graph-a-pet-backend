import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import InternalError, BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.codes.models import Code
from repository.query_builder import build_query, build_count, build_where


def create_code(data):
    logger.repository(f'data: {stringify(data)}')
    try:
        today = datetime.today()
        code = Code(
            id=f"{uuid.uuid4()}",
            code=data.get('code'),
            ref_table=data.get('ref_table'),
            ref_id=data.get('ref_id')
        )
        db.session.add(code)
        db.session.commit()
        return code.to_dict()
    except Exception as e:
        logger.error(e)
        raise e



def get_codes(common_search):
    try:
        query = build_query(table="codes", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(Code).from_statement(text(query))
        codes = db.session.execute(manager).scalars()
        return [code.to_dict() for code in codes]
    except Exception as e:
        logger.error(e)
        raise e


def get_filtered_codes(filters,):
    results = select(Code).from_statement(text(
        f"\
            SELECT  * \
            FROM codes \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    codes = db.session.execute(results).scalars()
    return [code.to_dict() for code in codes]

def get_total_items(common_search):
    try:
        query = build_count(table="codes", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e


def get_code(id):
    try:
        code = Code.query.get(id)
        logger.check(code)
        if code == None :
            raise NotFoundError('code_not_found')
        return code.to_dict()
    except Exception as e:
        logger.error(e)
        raise e 