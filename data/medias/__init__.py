import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import InternalError, BadRequest, NotFoundError
from data import db
from libs.logger import logger, stringify
from data.medias.models import Media
from data.query_builder import build_query, build_count, build_where


def create_media(data):
    logger.data(f'data: {stringify(data)}')
    try:
        today = datetime.today()
        media = Media(
            id=f"{uuid.uuid4()}",
            type=data.get('type'),
            url=data.get('url'),
            scope = data.get('scope'),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ref_id=data.get('ref_id')
        )
        db.session.add(media)
        db.session.commit()
        return media.to_dict()
    except Exception as e:
        logger.error(e)
        raise e


def update_media(id, data):
    logger.data(
        f"id: {id}\n"
        f"dta: {stringify(data)}"
    )
    try:
        media_model = db.session.query(Media).filter(Media.id == id)
        if not media_model:
            raise NotFoundError(f"no media found with id: {id}")
        media_old = media_model.first().to_dict()
        media_model.update(data)
        db.session.commit()
        media = {**media_old, **media_model.first().to_dict()}
        logger.check(f'media: {stringify(media)}')
        return media
    except Exception as e:
        logger.error(e)
        raise e


def get_medias(common_search):
    try:
        query = build_query(table="medias", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        manager = select(Media).from_statement(text(query))
        medias = db.session.execute(manager).scalars()
        return [pet.to_dict() for pet in medias]
    except Exception as e:
        logger.error(e)
        raise e


def get_filtered_medias(filters,):
    results = select(Media).from_statement(text(
        f"\
            SELECT  * \
            FROM medias \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    medias = db.session.execute(results).scalars()
    return [media.to_dict() for media in medias]

def get_total_items(common_search):
    try:
        query = build_count(table="medias", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e


def get_media(id):
    return Media.query.get(id).to_dict()
