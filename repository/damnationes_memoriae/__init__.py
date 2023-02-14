import uuid
from datetime import datetime
import psycopg2
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import select, text, Table, MetaData
from datetime import datetime, date
from repository import db, inspector
from repository.users.models import UserRole
from utils.logger import logger, stringify
from repository.damnationes_memoriae.models import DamnationesMemoriae
from controller.errors import BadRequest, NotFoundError
from repository.query_builder import build_count,  build_query, build_restore, tables_common_properties
import pydash as py_

def create_damnatio_memoriae(data):
    logger.repository(f'putting {data} into the damnatio memoriae')
    try:
        today = datetime.today()
        damnatio_memoriae = DamnationesMemoriae(
            id=f"{uuid.uuid4()}",
            original_data=data["original_data"],
            original_table=data["original_table"],
            restore_after=data["restore_after"],
            restore_before=data["restore_before"],
            deleted_by=data["deleted_by"],
            created_at=today.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        db.session.add(damnatio_memoriae)
        db.session.commit()
        return damnatio_memoriae.to_dict()['id']
    except Exception as e:
        logger.error(e)
        raise e


def get_damnatio_memoriae(id):
    logger.repository(f"fetching {id}")
    try:
        memoriae_model = DamnationesMemoriae.query.get(id)
        if not memoriae_model:
            raise NotFoundError(f"no memory found with id: {id}")
        memoriae = memoriae_model.to_dict()
        logger.check(memoriae)
        return memoriae
    except Exception as e:
        logger.error(e)
        raise e


def get_damnationes_memoriae(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="damnationes_memoriae",
                            ordering=common_search["ordering"], filters=common_search['filters'], pagination=common_search['pagination'])
        logger.check(f"query: {query}")
        manager = select(DamnationesMemoriae).from_statement(text(query))
        damnationes_memoriae_model = db.session.execute(manager).scalars()
        damnationes_memoriae = [health_card.to_dict()
                                for health_card in damnationes_memoriae_model]
        logger.check(
            f"damnationes_memoriae found {len(damnationes_memoriae)}\n{stringify(damnationes_memoriae)}")
        return damnationes_memoriae
    except ProgrammingError as e:
        logger.error(e)
        exception = BadRequest(
            "The fields provided may contains syntax errors")
        exception.extension['extra'] = str(e)
        raise exception
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="damnationes_memoriae",
                            filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e


def restore_memoriae(id, user, force= False):
    logger.repository(f"{user['id']}({user['role']}) is restoring {id}")
    try:
        
        memoriae = get_damnatio_memoriae(id)
        if ( not force and len(db.session.query(DamnationesMemoriae).filter(DamnationesMemoriae.restore_before.any(id) | DamnationesMemoriae.restore_after.any(id) ).all()) > 0) :
            message= f'can\'t restore {id} becouse it was cancelled automatically by another entity'
            logger.error(message)
            raise BadRequest(message)
        if user['role'] != UserRole.ADMIN and memoriae['deleted_by'] != user['id'] :
            message= f"{user['id']}({user['role']}) can't restore {id}"
            logger.error(message)
            raise BadRequest(message)
        logger.check(f"found {stringify(memoriae)}")
        for b_id in memoriae['restore_before']: 
            restore_memoriae(b_id, user, True)
        try:        
            query = build_restore(
                memoriae['original_table'], memoriae['original_data'])
            db.session.execute(query)
            db.session.commit()
        except Exception as e:
            logger.error(e)
            raise BadRequest(f"{e}\ncould not restore {memoriae['original_data']} from {memoriae['original_table']}")
        for a_id in memoriae['restore_after']: 
            restore_memoriae(a_id, user, True)
        delete_memoriae(id)
        return memoriae['original_data'], memoriae['original_table']
    except sqlalchemy.exc.IntegrityError as e:
        if 'psycopg2.errors.UniqueViolation' in str(e):
            message = f'could not resotre {memoriae["original_data"]["id"]} to {memoriae["original_table"]} becouse it already exist'
        else:
            message = str(e.orig)
        logger.error(message)
        raise BadRequest(message)
    except Exception as e:
        logger.error(e)
        raise e


def delete_memoriae(id):
    logger.repository(f"id: {id}  remove")
    try:
        memoriae_model = db.session.query(
            DamnationesMemoriae).filter(DamnationesMemoriae.id == id)
        if not memoriae_model:
            raise NotFoundError(f"no memory found with id: {id}")
        memoriae_model.delete()
        db.session.commit()
        logger.check(f"deleted {id}")
    except Exception as e:
        logger.error(e)
        raise e


def get_tables_referencing_table(table_name):
    logger.info(f'getting al tables in which {table_name} is referenced')
    try:
        table_names = py_.keys(tables_common_properties)
        tables = []
        for name in table_names:
            candidates = inspector.get_foreign_keys(name)
            for candidate in candidates:
                if candidate['referred_table'] == table_name:
                    logger.check(candidate)
                    tables.append({"table": name, **candidate})

        logger.check(f"found {len(tables)} tables")
        return tables
    except Exception as e:
        logger.error(e)
        raise e


def get_all_related(table):
    try:

        # Find the tables that have a foreign key referencing the selected row
        is_fk_in = get_tables_referencing_table(table)
        has_fk_in = inspector.get_foreign_keys(table)

        logger.check(f'destroy before itself {is_fk_in}')
        logger.check(f'destroy after itself {has_fk_in}')
        inherit_delete = py_.keys(
            tables_common_properties.get(table).get('inherit_delete'))
        logger.check(inherit_delete)
        return py_.filter_(is_fk_in, lambda x: x['table'] in inherit_delete),  py_.filter_(has_fk_in, lambda x: x['referred_table'] in inherit_delete),
    except Exception as e:
        logger.error(e)
        raise e

def row_to_dict(row):
    row_dict = {column: getattr(row, column) for column in row.keys()}
    for key, value in row_dict.items():
        if isinstance(value, datetime) or isinstance(value, date):
            row_dict[key] = value.isoformat()
    return row_dict


def delete_row(id, table, data, user_id, skip_ids=[]):
    logger.repository(f"{user_id} is removing {id} from {table}")
    try:
        skip = [id, *skip_ids]
        restore_after = []
        restore_before = []
        destroy_before, destroy_after = get_all_related(table)
        logger.info(f"removing {id} from {table}\n"\
                    f"skip: {skip_ids}")
        metadata = MetaData(db.get_engine())
        for item in destroy_before:
            if should_delete(table, item['table'], data) :
                linked = Table(item["table"], metadata, autoload=True)
                rows = ( 
                    db.session.query(linked)
                    .filter(getattr(linked.c, tables_common_properties[table]["other_table_ref"])== id )
                    .all()
                )
                for row in rows:
                    if row["id"] not in skip:
                        temp_id, toskip = delete_row(
                            row["id"], item["table"], row_to_dict(row),user_id, skip
                        )
                        restore_after.append(temp_id)
                        skip = py_.uniq([*skip, *toskip])
        

        memoriae_id = create_damnatio_memoriae(
            {
                "original_data": data,
                "original_table": table,
                "restore_before": restore_before,
                "restore_after": restore_after,
                "deleted_by": user_id
            }
        )
        orig_table =Table(table, metadata, autoload=True)
        stmt = orig_table.delete().where(orig_table.c.id == id)
        db.session.execute(stmt)
        db.session.commit()
        logger.check(f"memoriae created : {memoriae_id}")
        for item in destroy_after:
            if should_delete(table, item['referred_table'], data) :
                linked = Table(item["referred_table"], metadata, autoload=True)
                rows = (
                    db.session.query(linked)
                    .filter(getattr(linked.c, "id") == data[item["constrained_columns"][0]])
                    .all()
                )
                for row in rows:
                    if row["id"] not in skip:
                        temp_id, toskip = delete_row(
                            row["id"], item["referred_table"], row_to_dict(
                                row), user_id, skip
                        )
                        restore_before.append(temp_id)
                        skip =  py_.uniq([*skip, *toskip])
        update_memoriae(memoriae_id, {"restore_before" : restore_before})
        return memoriae_id, skip
    except Exception as e:
        logger.error(e)
        raise e

def should_delete(base_table, related_table, data):
    inherit_delete = tables_common_properties.get(base_table, {}).get(
        "inherit_delete", {}).get(related_table, {})
    if inherit_delete.get("cond") == "all":
        return True
    return data.get(list(inherit_delete.get("cond").keys())[0]) == list(inherit_delete.get("cond").values())[0]


def update_memoriae(id, data):
    logger.repository(
        f"id: {id}\n"\
        f"dta: {stringify(data)}"
    )
    try: 
        memoriae_model = db.session.query(DamnationesMemoriae).filter(DamnationesMemoriae.id== id)
        if not memoriae_model:
            raise NotFoundError(f"no pet found with id: {id}")
        memoriae_old = memoriae_model.first().to_dict()
        memoriae_model.update(data)
        db.session.commit()
        memoriae= {**memoriae_old, **memoriae_model.first().to_dict()}
        logger.check(f'pet: {stringify(memoriae)}')
        return  memoriae
    except Exception as e:
        logger.error(e)
        raise e