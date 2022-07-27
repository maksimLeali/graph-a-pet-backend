
from ntpath import join
from typing import Dict
import pydash as py_
from libs.utils import camel_to_snake
from itertools import permutations
from libs.logger import logger, stringify

tables_common_properties = {
    "users": {
        "search_columns": [
            'first_name',
            'last_name',
            'email',
        ],
        "alias": "us",
        "other_table_ref": "user_id"
    },
    "pets": {
        "search_columns": [
            "name",
        ],
        "alias": "pt",
        "other_table_ref": "pet_id"

    },
    "pet_bodies": {
        "search_columns": ['breed'],
        "alias": "ptb",
        "other_table_ref": "body_id"
    },
    "coats": {
        "search_columns": ['pattern'],
        "alias": "ct",
        "other_table_ref": "coat_id"
    },
    "ownerships": {
        "search_columns": ['custody_level'],
        "alias": "ow",
        "bridge_table": True,
        "other_table_ref": "ownership_id"
    },
    "health_cards": {
        "search_columns": ["logs"],
        "alias": "hlc",
        "bridge_table": True,
        "other_table_ref": "health_card_id"
    },
    "treatments": {
        "search_columns": ["logs", "name"],
        "alias": "tr",
        "bridge_table": True,
        "other_table_ref": "treatment_id"
    }
}


def build_join(parent: str, join: dict):
    try:
        logger.input(
            "DATA | query_builder.py | build_join"
            f"\nparent: {parent} "
            f"\njoin: {stringify(join)}"
        )
        join_string = ""
        filters = []
        parent_alias = tables_common_properties[parent]['alias']
        join_keys = py_.keys(join)
        for key in join_keys:
            join_alias = tables_common_properties[key]['alias']
            join_string += f"JOIN {key} AS {join_alias} ON {parent_alias}.{tables_common_properties[key]['other_table_ref']} = {join_alias}.id " if not tables_common_properties[key].get(
                'bridge_table') == True else f"JOIN {key} AS {join_alias} ON {join_alias}.{tables_common_properties[parent]['other_table_ref']} = {parent_alias}.id "
            filter_keys = py_.keys(join[key])
            for f_key in filter_keys:
                if f_key == "lists":
                    lists = format_list_filters(
                        alias=join_alias, filters=join[key][f_key])
                    if len(lists) > 0:
                        filters.append(f" {lists} ")
                if f_key == "ranges":
                    ranges = format_range_filters(
                        alias=join_alias, filters=join[key][f_key])
                    if len(ranges) > 0:
                        filters.append(f" {ranges} ")
                if f_key == "fixed":
                    fixed = format_fixed_filters(
                        alias=join_alias, filters=join[key][f_key])
                    if len(fixed) > 0:
                        filters.append(f" {fixed} ")
                if f_key == "join":
                    join_result = build_join(parent=key, join=join[key][f_key])
                    for join_filter in join_result[1]:
                        filters.append(join_filter)
                    join_string += join_result[0]
        logger.output(
            "DATA | query_builder.py | build_join\n"
            f"join_string: {join_string} \n"
            f"filters: {stringify(filters)}"
        )
        return join_string, filters
    except Exception as e:
        logger.error(e)
        raise e
    
def format_and_filters (table: str, filters: dict, already_joined: list, join_string):
    logger.input(
        f"table: {table}\n"
        f"filters: {stringify(filters)}\n"
        f"already_joined: {already_joined}\n"
    )
    formatted_filters= ""
    try:
        alias = tables_common_properties[table]['alias']
        filters_to_format = []
        formatted_fixed_filters = format_fixed_filters(alias, filters.get("fixed"), "AND")
        formatted_list_filters = format_list_filters(alias, filters.get("lists"), "AND")
        formatted_range_filters = format_range_filters(alias, filters.get('ranges'))
        join_string, join_filters = build_deep_join(table, filters.get('join') , already_joined, join_string)
        join_string, formatted_or_filters = format_or_filters(table, filters.get('or'),already_joined, join_string)
        join_string, formatted_not_filters = format_not_filters(table, filters.get('not'),already_joined, join_string)
        if len(formatted_fixed_filters) > 0:
            filters_to_format.append(formatted_fixed_filters)
        if len(formatted_list_filters) > 0:
            filters_to_format.append(formatted_list_filters)
        if len(formatted_range_filters) > 0:
            filters_to_format.append(formatted_range_filters)
        if len(formatted_or_filters) > 0:
            filters_to_format.append(f"({formatted_or_filters})")
        if len(formatted_not_filters) > 0:
            filters_to_format.append(f"({formatted_not_filters})")
        if len(join_filters) > 0:
            filters_to_format.append(f"({' AND  '.join(join_filters)})")
        formatted_filters = ' AND  '.join(filters_to_format)
        logger.output(f"formatted_filters: {formatted_filters}")
    except Exception as e: 
        logger.warning(e)
        pass
    return join_string, formatted_filters
    
def format_or_filters (table: str, filters: dict, already_joined: list, join_string: list):
    logger.input(
        f"table: {table}\n"
        f"filters: {stringify(filters)}\n"
        f"already_joined: {already_joined}\n"
    )
    formatted_filters=""
    try: 
        alias = tables_common_properties[table]['alias']
        filters_to_format = []
        formatted_fixed_filters = format_fixed_filters(alias, filters.get("fixed"), "OR")
        formatted_list_filters = format_list_filters(alias, filters.get("lists"), "OR")
        formatted_range_filters = format_range_filters(alias, filters.get('ranges'))
        join_string, join_filters = build_deep_join(table, filters.get('join') , already_joined, join_string)
        join_string, formatted_and_filters = format_and_filters(table, filters.get('and'), already_joined, join_string)
        join_string, formatted_not_filters = format_not_filters(table, filters.get('not'), already_joined, join_string)
        if len(formatted_fixed_filters) > 0:
            filters_to_format.append(formatted_fixed_filters)
        if len(formatted_list_filters) > 0:
            filters_to_format.append(formatted_list_filters)
        if len(formatted_range_filters) > 0:
            filters_to_format.append(formatted_range_filters)
        if len(formatted_and_filters) > 0:
            filters_to_format.append(f"({formatted_and_filters})")
        if len(formatted_not_filters) > 0:
            filters_to_format.append(f"({formatted_not_filters})")
        if len(join_filters) > 0:
            filters_to_format.append(f"({ ' OR  '.join(join_filters)})")
        formatted_filters = ' OR  '.join(filters_to_format)
        logger.output(f"formatted_filters: {formatted_filters}")
    except Exception as e: 
        logger.warning(e)
        pass
    return join_string, formatted_filters
    
def format_not_filters (table: str, filters: dict, already_joined: list, join_string :list):
    logger.input(
        f"table: {table}\n"
        f"filters: {stringify(filters)}\n"
        f"already_joined: {already_joined}\n"
    )
    formatted_filters=""
    try:
        alias = tables_common_properties[table]['alias']
        filters_to_format = []
        formatted_fixed_filters = format_fixed_filters(alias, filters.get("fixed"), "OR")
        formatted_list_filters = format_list_filters(alias, filters.get("lists"), "OR")
        formatted_range_filters = format_range_filters(alias, filters.get('ranges'))
        join_string, join_filters = build_deep_join(table, filters.get('join') , already_joined, join_string)
        join_string, formatted_and_filters = format_and_filters(table, filters.get('and'), already_joined, join_string)
        join_string, formatted_or_filters = format_or_filters(table, filters.get('or'), already_joined, join_string)
        if len(formatted_fixed_filters) > 0:
            filters_to_format.append(formatted_fixed_filters)
        if len(formatted_list_filters) > 0:
            filters_to_format.append(formatted_list_filters)
        if len(formatted_range_filters) > 0:
            filters_to_format.append(formatted_range_filters)
        if len(formatted_and_filters) > 0:
            filters_to_format.append(f"({formatted_and_filters})")
        if len(formatted_or_filters) > 0:
            filters_to_format.append(f"({formatted_or_filters})")
        if len(join_filters) > 0:
            filters_to_format.append(f'({" OR " .join(join_filters)}')
        formatted_filters = f'NOT  ({" OR " .join(filters_to_format)})'
        logger.output(f"formatted_filters: {formatted_filters}")
    except Exception as e: 
        logger.warning(e)
        pass
    return join_string, formatted_filters

def format_range_filters(alias, filters: Dict[str, Dict[str, str]], operator: str= "AND") -> str:
    logger.input(
        "DATA | query_builder.py | format_range_filters\n"
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


def format_search_filter(alias, filters: Dict[str, list]) -> str: 
    logger.input(
        f"alias: {alias} \n"
        f"filters: {stringify(filters)}"
    )
    search_list= []
    formatted_search = ""
    try: 
        # search
        search_fields= filters.get("fields") if len(filters.get("fields"))> 0 else tables_common_properties[alias]['search_columns']
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
        logger.output(
            "DATA | query_builder.py | format_fixed_filters\n"
            f"formatted_filters: {stringify(formatted_filters)}"
        )
        logger.output(f"formatted_list_filters: {stringify(formatted_filters)}")
    except Exception as e:
        logger.warning(e)
        pass
    return formatted_filters


def build_where(table: str, filters: Dict[str, dict], search: str = "", search_fields: list = []) -> str:
    logger.input("DATA | query_builder.py | build_where"
                 f"\ntable: {table}, search: {search} in: {stringify(search_fields)}"
                 f"\nfilters: {stringify(filters)} ")
    alias = tables_common_properties[table]['alias']
    filters_to_format = []
    formatted_fixed_filters = format_fixed_filters(alias, filters.get("fixed"))
    formatted_list_filters = format_list_filters(alias, filters.get("lists"))
    formatted_range_filters = format_range_filters(alias, filters.get('ranges'))
    join_string, join_filters = build_deep_join(parent=table, join=filters.get('join'))
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
    query_where = f"{join_string} " \
        f"{'WHERE ' if len(formatted_filters) > 0 or len(search) >0 or len(join_filters) > 0  else ''}{ formatted_filters}"  \
        f"{' AND ' if len(formatted_filters) > 0 and len(formatted_search) > 0  else ''}{formatted_search}" \
        f"{' AND ' if ( (len(formatted_filters) > 0 and len(join_filters))  or ( len(formatted_search) > 0 and len(join_filters)> 0 ))  else ''}{'AND'.join(join_filters)}"
    logger.check(
        f"DATA | query_builder.py | build_where \n"
        f"query_where: {query_where}"
    )
    return query_where


def build_query(table: str, search, search_fields, pagination: Dict[str, int], ordering: Dict[str, str], filters: dict = {"fixed": {}, "lists": {}, "ranges": {}, "join": {}}):
    logger.input(
        f"DATA | query_builder.py | build_where\n"
        f"table: {table}, search: {search} in {stringify(search_fields)}\n"
        f"filters: {stringify(filters)}"
    )
    alias = tables_common_properties[table]['alias']
    query = f"SELECT {alias}.* " \
        f"FROM {table} AS {alias} " \
        f" {build_where(table, filters,search,  search_fields if len(search_fields)> 0 else tables_common_properties[table]['search_columns']) } " \
        f"ORDER BY {alias}.{ordering['order_by']} {ordering['order_direction'].upper()}, {alias}.id ASC " \
        f"LIMIT {pagination['page_size']} OFFSET {pagination['page_size'] * pagination['page']}"

    logger.check(f"DATA | query_builder.py | build_query\n"
                 f"query: {query}")
    return query


def build_count(table: str, search, search_fields, filters: dict = {"fixed": [], "lists": [], "ranges": []}):
    logger.input(
        f"DATA | query_builder.py | build_count"
        f"\ntable: {table}, search: {search} in {stringify(search_fields)}"
        f"\nfilters: {stringify(filters)}"
    )
    alias = tables_common_properties[table]['alias']
    query_count = f"SELECT COUNT({alias}.*) " \
        f"FROM {table} AS {alias}" \
        f" {build_where(table, filters,search,  search_fields if len(search_fields)> 0 else tables_common_properties[table]['search_columns']) }"
    logger.check(f"DATA | query_builder.py | build_count"
                 f"query_count: {query_count}")
    return query_count


def build_deep_query(table: str,  filters: dict = {"and": {}, "or": {}, "not": {}}):
    logger.input(
        f"DATA | query_builder.py | build_where\n"
        f"table: {table},"
        f"filters: {stringify(filters)}"
    )
    join_string, formatted_filters = build_deep_where(table, [table], [], filters)
    
    logger.info('§§§§§§§§§§§')
    logger.info(join_string)
    
    logger.info('§§§§§§§§§§§')
    logger.info(f"{stringify(formatted_filters)}")
    alias = tables_common_properties[table]['alias']
    joins_to_print= '\n'.join(join_string)
    query = f"SELECT {alias}.* " \
        f"FROM {table} AS {alias} " \
        f"{''.join(join_string)} " \
        f"WHERE {formatted_filters} " \
        # f"ORDER BY {alias}.{ordering['order_by']} {ordering['order_direction'].upper()}, {alias}.id ASC " \
        # f"LIMIT {pagination['page_size']} OFFSET {pagination['page_size'] * pagination['page']}"
    logger.critical(
        f"SELECT {alias}.* \n" \
        f"FROM {table} AS {alias} \n" \
        f"{joins_to_print} \n" \
        f"WHERE {formatted_filters} \n" \
    )
    logger.critical(f"query: {stringify(query)}")
    # logger.check(f"DATA | query_builder.py | build_query\n"
    #              f"query: {query}")
    # return query

def build_deep_where(table: str, already_joined: list, join_string: list, filters: Dict[str, dict] = {"or": None, "and": None, "not": None }) -> str:
    logger.input(
        f"table: {table}\n"
        f"already_joined: {already_joined}\n"
        f"join_string: {join_string}\n"
        f"filters: {stringify(filters)}"
    )
    
    join_string, format_and = format_and_filters(table, filters.get('and'), already_joined, join_string)
    join_string, format_or = format_or_filters(table, filters.get('or'), already_joined, join_string)
    join_string, format_not = format_not_filters(table, filters.get('not'), already_joined, join_string)
    
    filters_to_format = []
    if(len(format_and)> 0):
        filters_to_format.append(format_and)
    if(len(format_or)> 0):
        filters_to_format.append(format_or)
    if(len(format_not)> 0):
        filters_to_format.append(format_not)
    formatted_filters = f" ({ ') AND ('.join(filters_to_format)})"    
    return join_string, formatted_filters
    
def build_deep_join (parent: str, join:  dict, already_joined: list, join_string: list):
    try:
        logger.info(
            "DATA | query_builder.py | build_join"
            f"\nparent: {parent} "
            f"\njoin: {stringify(join)}"
            f"\nalredy_joined: {already_joined}"
        )
        
        filters = []
        parent_alias = tables_common_properties[parent]['alias']
        join_keys = py_.keys(join)
        for key in join_keys:
            join_alias = tables_common_properties[key]['alias']
            if(not key in already_joined):
                already_joined.append(key)
                logger.info(
                    '§----§§§§-----§§§§§§§§§§§§§\n'
                    f'key: {key}\n'
                    f"join_alias: {join_alias}\n"
                    f"is_brtidge: {tables_common_properties[key].get('bridge_table')}"
                )
                
                join_string.append(f"JOIN {key} AS {join_alias} ON {parent_alias}.{tables_common_properties[key]['other_table_ref']} = {join_alias}.id " if (tables_common_properties[key].get(
                'bridge_table') != True) else f"JOIN {key} AS {join_alias} ON {join_alias}.{tables_common_properties[parent]['other_table_ref']} = {parent_alias}.id " )
                logger.critical(
                     '§----§§§§-----§§§§§§§§§§§§§\n'
                    f"{join_string}"
                    )
            
            join_string, formatted_filters =build_deep_where(key,already_joined,join_string, join[key])
            logger.error(stringify(formatted_filters))
            filters.append(formatted_filters)
        
        logger.critical(
            f"join_string: {join_string}\n"
            f"join_filters: {stringify(filters)}"
        )
        return join_string, filters 
    except Exception as e:
        logger.error(e)
        raise e