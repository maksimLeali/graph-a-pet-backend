from enum import Enum
from repository.pets import get_all_pets
import repository.damnationes_memoriae as damnationes_memoriae_data
from math import ceil
from repository.users import get_all_active_users, get_all_users
from utils.logger import logger, stringify
from datetime import datetime, date
from sqlalchemy import Table, MetaData
from repository import db
from repository.query_builder import tables_common_properties
import pendulum
import pydash as py_


# def create_damnatio_memoriae(data):
#     logger.domain(f'data: {stringify(data)}')
#     try:
#         damnatio_memoriae = damnationes_memoriae_data.create_damnatio_memoriae(data)
#         return damnatio_memoriae
#     except Exception as e:
#         logger.error(e)
#         raise e


# def update_damnatio_memoriae(id, data):
#     logger.domain(
#         f"id: {id}\n"
#         f"data: {stringify(data)}"
#     )
#     try:
#         damnatio_memoriae = damnationes_memoriae_data.update_damnatio_memoriae(id, data)
#         logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
#         return damnatio_memoriae
#     except Exception as e:
#         logger.error(e)
#         raise e

def get_paginated_damnationes_memoriae(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        damnationes_memoriae = get_damnationes_memoriae(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (damnationes_memoriae, pagination)
    except Exception as e:
        logger.error(e)
        raise e
  
def get_damnationes_memoriae(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        damnationes_memoriae = damnationes_memoriae_data.get_damnationes_memoriae(common_search)
        logger.output(f"damnationes_memoriae: {len(damnationes_memoriae)}")
        return damnationes_memoriae
    except Exception as e:
        logger.error(e)
        raise e


def get_damnatio_memoriae(id):
    logger.domain(f"id: {id}")
    try:
        damnatio_memoriae = damnationes_memoriae_data.get_damnatio_memoriae(id)
        logger.check(f"damnatio_memoriae: {stringify(damnatio_memoriae)}")
        return damnatio_memoriae
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = damnationes_memoriae_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        pagination = {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
        logger.output(f"pagination: {stringify(pagination)}")
        return pagination
    except Exception as e:
        logger.error(e)
        raise e


def restore_memoriae(id):
    logger.domain(f"restoring {id}")
    try:   
        restored, table= damnationes_memoriae_data.restore_memoriae(id)
        logger.check(f"restored {stringify(restored)}")
        return restored, table
    except Exception as e: 
        logger.error(e)
        raise e
    
def row_to_dict(row):
    row_dict = {column: getattr(row, column) for column in row.keys()}
    for key, value in row_dict.items():
        if isinstance(value, datetime) or isinstance(value, date ):
            row_dict[key] = value.isoformat()
    return row_dict
    
def delete_row(id, table, data, skip_ids= []):
    logger.domain(f'removing {id} from {table}')
    try:
        destroy_before, destroy_after = damnationes_memoriae_data.get_all_related(table)
        skip = [id, *skip_ids]
        restore_after = []
        restore_before = []
        logger.warning(f"{id}, {skip_ids}")
        for item in destroy_before : 
            metadata = MetaData(db.get_engine())
            linked = Table(item['table'], metadata, autoload=True)
            rows = db.session.query(linked).filter(getattr(linked.c,tables_common_properties[table]['other_table_ref']) == id).all()
            for row in rows:
                logger.critical(row['id'] in skip)
                if row['id'] not in skip :
                    temp_id, toskip = delete_row(row['id'], item['table'],row_to_dict(row), skip)
                    restore_after.append(temp_id)
                    skip= [*skip, *toskip]
            
        for item in destroy_after : 
            metadata = MetaData(db.get_engine())
            linked = Table(item['referred_table'], metadata, autoload=True)
            current = Table(table, metadata, autoload=True)
            rows = db.session.query(linked).filter(getattr(linked.c,"id") == getattr(current.c,item['constrained_columns'][0])).all()
            for row in rows:
                logger.critical(f"table: {item['referred_table']} row: {row}, id: {row['id']} , skip: {skip_ids}")
                logger.critical(row['id'] in skip)
                if row['id'] not in skip :
                    temp_id, toskip = delete_row(row['id'], item['referred_table'],row_to_dict(row), skip)
                    restore_after.append(temp_id)
                    skip= [*skip, *toskip]
                    
        memoriae_id = damnationes_memoriae_data.create_damnatio_memoriae({"original_data": data, 'original_table': table, "restore_before": restore_before, "restore_after" : restore_after})
        return memoriae_id, skip
    except Exception as e: 
        logger.error(e)
        raise e

