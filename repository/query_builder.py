from typing import Dict
import pydash as py_
from controller.errors import BadRequest
from utils import camel_to_snake
from itertools import permutations
from utils.logger import logger, stringify
from config import cfg
tables_common_properties = cfg.get('db_scheme')

def build_join (parent: str, join:  dict, already_joined: list, join_string: list):
    try:
        logger.input(
            f"\nparent: {parent} "
            f"\njoin: {stringify(join)}"
            f"\nalredy_joined: {already_joined}"
        )
        
        filters = []
        join_keys = py_.keys(join)
        for key in join_keys:
            if(not key in already_joined):
                parent_alias = tables_common_properties[parent]['alias']
                join_alias = tables_common_properties[key]['alias']
                already_joined.append(key)
                if(parent in tables_common_properties[key]['children']):
                    joining_string = f"JOIN {key} AS {join_alias} ON {parent_alias}.{tables_common_properties[key]['other_table_ref']} = {join_alias}.id " 
                elif (key in tables_common_properties[parent]['children']):
                    joining_string = f"JOIN {key} AS {join_alias} ON {join_alias}.{tables_common_properties[parent]['other_table_ref']} = {parent_alias}.id " 
                else :
                    logger.error(f'no links between {parent} and {key}')
                    error = BadRequest(f'no_links_between_tables')              
                    error.extension['extra']= f" no links between {parent} and {key}"
                    raise error
                join_string.append(joining_string)
            join_string, formatted_filters =build_where(key,already_joined,join_string, join[key])
            filters.append(formatted_filters)
        logger.output(
            f"join_string: {join_string}\n"
            f"join_filters: {stringify(filters)}"
        )
        return join_string, filters 
    except Exception as e:
        logger.error(e)
        raise e
def build_where(table: str, already_joined: list, join_string: list, filters: Dict[str, dict] = {"or": None, "and": None, "not": None }) -> str:
    logger.input(
        f"table: {table}\n"
        f"already_joined: {already_joined}\n"
        f"join_string: {join_string}\n"
        f"filters: {stringify(filters)}"
    )
    
    join_string, format_and = format_main_filters(table, filters.get('and'), already_joined, join_string, "AND")
    join_string, format_or = format_main_filters(table, filters.get('or'), already_joined, join_string, "OR")
    join_string, format_not = format_main_filters(table, filters.get('not'), already_joined, join_string, "NOT")
    
    filters_to_format = []
    if(len(format_and)> 0):
        filters_to_format.append(format_and)
    if(len(format_or)> 0):
        filters_to_format.append(format_or)
    if(len(format_not)> 0):
        filters_to_format.append(format_not)
    formatted_filters = f" ({ ') AND ('.join(filters_to_format)})"
    logger.output(
        f"formatted_filters: {formatted_filters}\n"
        f"join_string: {join_string}"
    )
    return join_string, formatted_filters

def format_main_filters (table: str, filters: dict, already_joined: list, join_string :list, operator: str):
    logger.info(
        f"table: {table}\n"
        f"filters: {stringify(filters)}\n"
        f"operator: {operator}\n"
        f"already_joined: {already_joined}\n"
    )
    formatted_filters=""
    try:
        alias = tables_common_properties[table]['alias']
        filters_to_format = []
        formatted_fixed_filters = format_fixed_filters(alias, filters.get("fixed"), operator if operator != "NOT" else "OR")
        formatted_list_filters = format_list_filters(alias, filters.get("lists"), operator if operator != "NOT" else "OR")
        formatted_range_filters = format_range_filters(alias, filters.get('ranges'))
        formatted_search_filters = format_search_filters(table, filters.get('search'))
        join_string, join_filters = build_join(table, filters.get('join') , already_joined, join_string)
        join_string, formatted_and_filters = format_main_filters(table, filters.get('and'), already_joined, join_string, "AND")
        join_string, formatted_or_filters = format_main_filters(table, filters.get('or'), already_joined, join_string, "OR")
        join_string, formatted_not_filters = format_main_filters(table, filters.get('not'), already_joined, join_string, "NOT")     
        if len(formatted_fixed_filters) > 0:
            filters_to_format.append(formatted_fixed_filters)
        if len(formatted_list_filters) > 0:
            filters_to_format.append(formatted_list_filters)
        if len(formatted_range_filters) > 0:
            filters_to_format.append(formatted_range_filters)
        if len(formatted_search_filters) > 0:
            filters_to_format.append(formatted_search_filters)
        if len(formatted_and_filters) > 0:
            filters_to_format.append(f"({formatted_and_filters})")
        if len(formatted_or_filters) > 0:
            filters_to_format.append(f"({formatted_or_filters})")
        if len(formatted_not_filters) > 0:
            filters_to_format.append(f"({formatted_not_filters})")
        if len(join_filters) > 0:
            temp_operator = operator if operator != "NOT" else "OR"
            filters_to_format.append(f'({f" {temp_operator} " .join(join_filters)})')
        if(operator == 'NOT'):
            formatted_filters = f'NOT  ({" OR " .join(filters_to_format)})'
        elif(operator == 'OR'): 
            formatted_filters = ' OR  '.join(filters_to_format)
        else: 
            formatted_filters = ' AND  '.join(filters_to_format)
        logger.check(f"formatted_filters: {formatted_filters}")
    except BadRequest as e:
        logger.error(e)
        raise e
    except Exception as e: 
        logger.warning(e)
        pass
    return join_string, formatted_filters

def format_range_filters(alias, filters: Dict[str, Dict[str, str]], operator: str= "AND") -> str:
    logger.input(
        f"alias: {alias} \n"
        f"filters: {stringify(filters)}"
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            quote = "'"
            formatted_filters += \
                f"{alias}.{camel_to_snake(key)}" \
                f"{(' > ' + quote + str(filters[key]['min']) )+ quote if  'min' in filters[key] else '' }" \
                f"{ f' {operator} '  +alias+'.'+ camel_to_snake(key) if len(filters[key]) > 1 else '' }" \
                f"{(' < '+ quote + str(filters[key]['max']) ) + quote if  'max' in filters[key] else '' }" \
                f"{f' {operator} ' if i < len(filters.keys()) else '' }"
        logger.input(f"formatted_range_filters: {stringify(formatted_filters)}")
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def format_search_filters(table, filters: Dict[str, list]) -> str: 
    logger.input(
        f"alias: {table} \n"
        f"filters: {stringify(filters)}"
    )
    search_list= []
    formatted_search = ""
    try: 
        alias = tables_common_properties[table]['alias']
        search_fields= filters.get("fields") if len(filters.get("fields"))> 0 else tables_common_properties[table]['search_columns']
        if  filters.get("value") and len(filters.get("value")) >0 :
            to_permutate = filters.get("value").split(' ')
            for i in range(len(to_permutate)):
                search_list.extend([" ".join(val)
                                for val in permutations(to_permutate, i+1)])
        for i, value in enumerate(search_list, start=1):
            for k, field in enumerate(search_fields, start=1):
                formatted_search += f"{'(' if i==1 and k==1 else ''} "  \
                f"LOWER({alias}.{camel_to_snake(field)}) LIKE LOWER('%{value}%') "  \
                    f"{'OR' if i <  len(search_list) or k < len(search_fields)  else ')'} "
        formatted_search += f" OR {alias}.id =  LOWER('{value}')"
        logger.output(f'formatted_search: {formatted_search}')
    except Exception as e: 
        logger.warning(e)
        pass
    return formatted_search

def format_fixed_filters(alias, filters: Dict[str, str], operator: str = "AND") -> str:
    logger.input(
        "DATA | query_builder.py | format_fixed_filters\n"
        f"alias: {alias} \n"
        f"filters: {stringify(filters)}"
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            formatted_filters += f"{alias}.{camel_to_snake(key)} = '{filters[key]}' {f' {operator} ' if i < len(filters.keys()) else '' }"
        logger.output(f"formatted_fixed_filters: {stringify(formatted_filters)}")
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def format_list_filters(alias, filters: Dict[str, list], operator: str = "AND") -> str:
    logger.input(
        "DATA | query_builder.py | format_list_filters\n"
        f"alias: {alias} \n"
        f"filters: {stringify(filters)}"
    )
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            separetor = "', '"
            formatted_filters += f"{alias}.{camel_to_snake(key)} in ('{ separetor.join(filters[key])}') {f' {operator} ' if i < len(filters.keys()) else '' }"
        logger.output(f"formatted_list_filters: {stringify(formatted_filters)}")
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def build_count(table: str, filters: dict = {"fixed": [], "lists": [], "ranges": []}):
    
    logger.input(
        f"table: {table},"
        f"filters: {stringify(filters)}"
    )
    try: 
        join_string, formatted_filters = build_where(table, [table], [], filters)
        alias = tables_common_properties[table]['alias']
        joins_to_print= '\n'.join(join_string)

        query_count = f"SELECT COUNT(DISTINCT({alias}.id)) " \
            f"FROM {table} AS {alias} " \
            f"{''.join(join_string)} " \
             f"{'WHERE' + formatted_filters if len(filters)> 0 else ''} "  \
 
                
        logger.check(
            f"SELECT COUNT(DISTINCT({alias}.id)) \n" \
            f"FROM {table} AS {alias} \n" \
            f"{joins_to_print} \n" \
            f"{ 'WHERE' +  formatted_filters if len(filters)> 0 else ''} "  \
        )
        return query_count
    except Exception as e: 
        logger.error(e)
        raise e

def build_query(table: str,pagination: dict = {"page_size" : 20, "page": 0}, ordering: dict = {"order_by": "created_at", "order_direction": "ASC"}, filters: dict = {"and": {}, "or": {}, "not": {}}):
    logger.input(
        f"DATA | query_builder.py | build_where\n"
        f"table: {table},"
        f"filters: {stringify(filters)}"
    )
    try: 
        join_string, formatted_filters = build_where(table, [table], [], filters)
        alias = tables_common_properties[table]['alias']
        
        query = f"SELECT {alias}.*  "\
            f"FROM {table} AS {alias} "\
            f"{''.join(join_string)} "\
            f"{'WHERE' + formatted_filters if len(filters)> 0  else ''} "  \
            f"GROUP BY ({alias}.id) " \
            f"ORDER BY {alias}.{ordering['order_by']} {ordering['order_direction'].upper()}, {alias}.id ASC " \
            f"LIMIT {pagination['page_size']} OFFSET {pagination['page_size'] * pagination['page']}"
        
        logger.check(
            f"SELECT DISTINCT ({alias}.id), {alias}.*  \n" \
            f"FROM {table} AS {alias} \n" \
            f"{''.join(join_string)} \n" \
             f"{'WHERE' + formatted_filters if len(filters)> 0 else ''} \n"  \
            f"GROUP BY ({alias}.id) \n" \
            f"ORDER BY {alias}.{ordering['order_by']} {ordering['order_direction'].upper()}, {alias}.id ASC \n" \
            f"LIMIT {pagination['page_size']} \nOFFSET {pagination['page_size'] * pagination['page']}"
        )
        return query
    except Exception as e: 
        logger.error(e)
        raise e