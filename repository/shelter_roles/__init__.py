import uuid
from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text
from api.errors import InternalError, BadRequest, NotFoundError
from repository import db
from utils.logger import logger, stringify
from repository.shelter_roles.models import ShelterRole, RoleLevel
from repository.query_builder import build_query, build_count, build_where


def get_roles_for_user_on_shelter(user_id, shelter_id):
    logger.repository(f"user_id: {user_id} shelter_id: {shelter_id}")
    models = db.session.query(ShelterRole).filter(
        ShelterRole.user_id == user_id,
        ShelterRole.shelter_id == shelter_id,
    ).all()
    return [m.to_dict() for m in models]


def create_shelter_role(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()

        role_raw = data.get("role")
        enum_value = None
        if role_raw is not None:
            if isinstance(role_raw, RoleLevel):
                enum_value = role_raw
            else:
                try:
                    enum_value = RoleLevel[role_raw.upper()]
                except KeyError:
                    raise BadRequest(f"Invalid role: {role_raw}")

        shelter_role = ShelterRole(
            id=f"{uuid.uuid4()}",
            user_id=data["user_id"],
            shelter_id=data["shelter_id"],
            role=enum_value,
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
        db.session.add(shelter_role)
        db.session.commit()
        return shelter_role.to_dict()
    except Exception as e:
        logger.error(e)
        raise e

def update_shelter_role(id, data):
    logger.repository(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        if "role" in data and data["role"] is not None and not isinstance(data["role"], RoleLevel):
            try:
                data["role"] = RoleLevel[data["role"].upper()]
            except KeyError:
                raise BadRequest(f"Invalid role: {data['role']}")

        shelter_role_model = db.session.query(ShelterRole).filter(ShelterRole.id == id)
        if not shelter_role_model.first():
            raise NotFoundError(f"no shelter_role found with id: {id}")
        shelter_role_old = shelter_role_model.first().to_dict()
        shelter_role_model.update(data)
        db.session.commit()
        shelter_role = {**shelter_role_old, **shelter_role_model.first().to_dict()}
        logger.check(f'shelter_role: {stringify(shelter_role)}')
        return shelter_role
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_roles(common_search):
    try:
        query = build_query(table="shelter_roles",ordering=common_search["ordering"],filters= common_search['filters'], pagination=common_search['pagination'] )
        manager = select(ShelterRole).from_statement(text(query))
        ownershps = db.session.execute(manager).scalars()
        return [pet.to_dict() for pet in ownershps]
    except Exception as e: 
        logger.error(e)
        raise e

def get_filtered_shelter_roles(filters,):
    results = select(ShelterRole).from_statement(text(
        f"\
            SELECT  * \
            FROM shelter_roles \
            { '' if len(filters)== 0 else build_where(filters) } \
        "))
    shelter_roles = db.session.execute(results).scalars()
    return [shelter_role.to_dict() for shelter_role in shelter_roles]

def get_total_items(common_search):
    try:
        query = build_count(table="shelter_roles",filters= common_search['filters'] )
        result = db.session.execute(query).first()
        return result[0] if result!= None else 0
    except ProgrammingError as e: 
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e

def get_shelter_role(id):
    logger.repository(f"id: {id}")
    try:
        shelter_role_model = ShelterRole.query.get(id)
        if not shelter_role_model:
            raise NotFoundError(f"no pet found with id: {id}")
        shelter_role= shelter_role_model.to_dict()
        return shelter_role
    except Exception as e:
        logger.error(e)
        raise e

def delete_shelter_role(id, ):
    logger.repository(f"id: {id}  remove")
    try: 
        shelter_role_model = db.session.query(ShelterRole).filter(ShelterRole.id == id)
        if not shelter_role_model:
            raise NotFoundError(f"no shelter_role found with id: {id}")
        shelter_role_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e: 
        logger.error(e)
        raise e
    