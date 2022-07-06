
from typing import Dict
import pydash as py_
from api.errors import InternalError
from libs.utils import camel_to_snake
from itertools import permutations
from libs.logger import logger, stringify

tables_common_properties = {
    "users":{ 
        "search_columns": [
            'first_name', 
            'last_name', 
            'email', 
            ],
        "alias": "us",
        "other_table_ref": "user_id"
        },
    "pets":{ 
        "search_columns": [
            "name", 
            ],
        "alias": "pt",
        "other_table_ref":"pet_id"
        
        },
    "pet_bodies":{ 
        "search_columns": ['breed'],
        "alias": "ptb",
        "other_table_ref": "body_id"
        },
    "coats":{ 
        "search_columns": ['pattern'],
        "alias": "ct",
        "other_table_ref": "coat_id"
        },
    "ownerships":{ 
        "search_columns": ['custody_level'],
        "alias": "ow",
        "other_table_ref": "ownership_id"
        },
}

def build_join(parent: str, join: dict):
    try: 
        logger.input(
            "DATA | query_builder.py | build_join" \
            f"\nparent: {parent} " \
            f"\njoin: {stringify(join)}"
        )
        join_string = ""
        filters= []
        parent_alias= tables_common_properties[parent]['alias']
        join_keys= py_.keys(join)
        for key in join_keys:
            join_alias=tables_common_properties[key]['alias']
            join_string += f"JOIN {key} AS {join_alias} ON {parent_alias}.{tables_common_properties[key]['other_table_ref']} = {join_alias}.id "
            filter_keys = py_.keys(join[key])
            for f_key in filter_keys :
                if f_key == "lists" :
                    lists = format_list_filters(alias= join_alias, filters=join[key][f_key] )
                    if len(lists)> 0:
                        filters.append(f" {lists} ")
                if f_key == "ranges" :
                    ranges = format_range_filters(alias= join_alias, filters=join[key][f_key] )
                    if len(ranges)> 0:
                        filters.append(f" {ranges} ")
                if f_key == "fixeds" :
                    fixeds=format_fixed_filters(alias= join_alias, filters=join[key][f_key] )
                    if len(fixeds)> 0:
                        filters.append(f" {fixeds} ")
                if f_key == "join" :
                    join_result = build_join(parent=key, join=join[key][f_key])
                    for join_filter in join_result[1]:
                        filters.append(join_filter)
                    join_string+= join_result[0]
        logger.output(
            "DATA | query_builder.py | build_join\n" \
            f"join_string: {join_string} \n" \
            f"filters: {stringify(filters)}"
        )
        return join_string, filters
    except Exception as e: 
        logger.error(e)
        raise e


def format_range_filters(alias,filters: Dict[str, Dict[str, str]]) -> str:
    logger.input(
        "DATA | query_builder.py | format_range_filters\n" \
        f"alias: {alias} \n" \
        f"filters: {stringify(filters)}" 
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            quote = "'"
            formatted_filters += \
                f"{alias}.{camel_to_snake(key)}" \
                f"{(' > ' + quote + str(filters[key]['min']) )+ quote if  'min' in filters[key] else '' }" \
                f"{' AND ' +alias+'.'+ camel_to_snake(key) if len(filters[key]) > 1 else '' }" \
                f"{(' < '+ quote + str(filters[key]['max']) ) + quote if  'max' in filters[key] else '' }" \
                f"{' AND ' if i < len(filters.keys()) else '' }"
        logger.output(
             "DATA | query_builder.py | format_range_filters\n" \
            f"formatted_filters: {stringify(formatted_filters)}"
        )
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def format_fixed_filters(alias,filters: Dict[str, str]) -> str:
    logger.input(
        "DATA | query_builder.py | format_fixed_filters\n" \
        f"alias: {alias} \n" \
        f"filters: {stringify(filters)}" 
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            formatted_filters += f"{alias}.{camel_to_snake(key)} = '{filters[key]}' {'AND' if i < len(filters.keys()) else '' }"
        logger.output(
             "DATA | query_builder.py | format_fixed_filters\n" \
            f"formatted_filters: {stringify(formatted_filters)}"
        )
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def format_list_filters(alias,filters: Dict[str, list]) -> str:
    logger.input(
        "DATA | query_builder.py | format_list_filters\n" \
        f"alias: {alias} \n" \
        f"filters: {stringify(filters)}" 
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            separetor = "', '"
            formatted_filters += f"{alias}.{camel_to_snake(key)} in ('{ separetor.join(filters[key])}') {'AND' if i < len(filters.keys()) else '' }"
        logger.output(
             "DATA | query_builder.py | format_fixed_filters\n" \
            f"formatted_filters: {stringify(formatted_filters)}"
        )
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters

def build_where(table: str ,filters: Dict[str, dict] = {"fixeds": None, "lists": None, "ranges": None}, search: str = "", search_fields: list = []) -> str:
    logger.input("DATA | query_builder.py | build_where" \
                 f"\ntable: {table}, search: {search} in: {stringify(search_fields)}" \
                 f"\nfilters: {stringify(filters)} " )
    alias = tables_common_properties[table]['alias']
    filters_to_format = []
    formatted_fixed_filters = format_fixed_filters(alias,filters["fixeds"])
    formatted_list_filters = format_list_filters(alias,filters["lists"])
    formatted_range_filters = format_range_filters(alias,filters['ranges'])
    join_string, join_filters = build_join(parent=table, join= filters['join'])
    formatted_search = ""
    search_list = []

    if len(formatted_fixed_filters) > 0:
        filters_to_format.append(formatted_fixed_filters)
    if len(formatted_list_filters) > 0:
        filters_to_format.append(formatted_list_filters)
    if len(formatted_range_filters) > 0:
        filters_to_format.append(formatted_range_filters)
    formatted_filters = ' AND '.join(filters_to_format)

    if len(search) > 0:
        to_permutate = search.split(' ')
        for i in range(len(to_permutate)):
            search_list.extend([" ".join(val)
                               for val in permutations(to_permutate, i+1)])
    for i, value in enumerate(search_list, start=1):
        for k, field in enumerate(search_fields, start=1):
            formatted_search += f"{'(' if i==1 and k==1 else ''} "  \
                f"LOWER({camel_to_snake(field)}) LIKE LOWER('%{value}%') "  \
                f"{'OR' if i <  len(search_list) or k < len(search_fields)  else ')'} "
    query_where= f"{join_string} " \
        f"{'WHERE ' if len(formatted_filters) > 0 or len(search) >0 or len(join_filters) > 0  else ''}{ formatted_filters}"  \
        f"{' AND ' if len(formatted_filters) > 0 and len(formatted_search) > 0  else ''}{formatted_search}" \
        f"{' AND ' if ( (len(formatted_filters) > 0 and len(join_filters))  or ( len(formatted_search) > 0 and len(join_filters)> 0 ))  else ''}{'AND'.join(join_filters)}"
    logger.check(
        f"DATA | query_builder.py | build_where \n"\
        f"query_where: {query_where}"
    )
    return query_where


def build_query(table: str, search, search_fields, pagination: Dict[str, int], ordering: Dict[str, str], filters: dict = {"fixeds": {}, "lists": {}, "ranges": {},"join": {}} ):
    logger.input(
        f"DATA | query_builder.py | build_where\n" \
        f"table: {table}, search: {search} in {stringify(search_fields)}\n" \
        f"filters: {stringify(filters)}"
    )
    alias = tables_common_properties[table]['alias']
    query= f"SELECT {alias}.* " \
        f"FROM {table} AS {alias} " \
        f" {build_where(table, filters,search,  search_fields if len(search_fields)> 0 else tables_common_properties[table]['search_columns']) } " \
        f"ORDER BY {alias}.{ordering['order_by']} {ordering['order_direction'].upper()}, {alias}.id ASC " \
        f"LIMIT {pagination['page_size']} OFFSET {pagination['page_size'] * pagination['page']}"
        
    logger.check(f"DATA | query_builder.py | build_query\n" \
                  f"query: {query}")
    return query
        
def build_count(table: str, search, search_fields, filters: dict = {"fixeds": [], "lists": [], "ranges": []}):
    logger.input(
        f"DATA | query_builder.py | build_count" \
        f"\ntable: {table}, search: {search} in {stringify(search_fields)}" \
        f"\nfilters: {stringify(filters)}"
    )
    alias = tables_common_properties[table]['alias']
    query_count= f"SELECT COUNT({alias}.*) " \
        f"FROM {table} AS {alias}" \
        f" {build_where(table, filters,search,  search_fields if len(search_fields)> 0 else tables_common_properties[table]['search_columns']) }"
    logger.check(f"DATA | query_builder.py | build_count" \
                  f"query_count: {query_count}")
    return query_count
        