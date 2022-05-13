from typing import Dict
import pydash as py_
from libs.utils import camel_to_snake
from itertools import permutations
from libs.logger import logger

deafult_search_columns: dict = {
    "users": ['first_name', 'last_name', 'email', ],
    "pets": ["name", "breed"],
    "coats": ['pattern'],
    "ownerships": ['role']
}


def format_range_filters(filters: Dict[str, Dict[str, str]]) -> str:
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            quote = "'"
            formatted_filters += \
                f"{camel_to_snake(key)}" \
                f"{(' > ' + quote + str(filters[key]['min']) )+ quote if  'min' in filters[key] else '' }" \
                f"{' AND ' + camel_to_snake(key) if len(filters[key]) > 1 else '' }" \
                f"{(' < '+ quote + str(filters[key]['max']) ) + quote if  'max' in filters[key] else '' }" \
                f"{' AND ' if i < len(filters.keys()) else '' }"
    except Exception as e:
        pass
    return formatted_filters


def format_fixed_filters(filters: Dict[str, str]) -> str:
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            formatted_filters += f"{camel_to_snake(key)} = '{filters[key]}' {'AND' if i < len(filters.keys()) else '' }"
    except Exception as e:
        pass
    return formatted_filters


def format_list_filters(filters: Dict[str, list]) -> str:
    formatted_filters = ""
    try:
        for i, key in enumerate(filters.keys(), start=1):
            separetor = "', '"
            formatted_filters += f"{camel_to_snake(key)} in ('{ separetor.join(filters[key])}') {'AND' if i < len(filters.keys()) else '' }"
    except Exception as e:
        pass
    return formatted_filters


def build_where(filters: Dict[str, dict] = {"fixeds": None, "lists": None, "ranges": None}, search: str = "", search_fields: list = []) -> str:
    filters_to_format = []
    formatted_fixed_filters = format_fixed_filters(filters["fixeds"])
    formatted_list_filters = format_list_filters(filters["lists"])
    formatted_range_filters = format_range_filters(filters['ranges'])
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
                f"{'OR' if i <  len(search_list) or k < len(search_fields) else ')'} "
    return f"{'WHERE ' if len(formatted_filters) > 0 or len(search) >0 else ''}{ formatted_filters}"  \
        f"{' AND ' if len(formatted_filters) > 0 and len(formatted_search) > 0  else ''}{formatted_search}"


def build_simple_query(table: str, search, search_fields, pagination: Dict[str, int], ordering: Dict[str, str], filters: dict = {"fixeds": {}, "lists": {}, "ranges": {}}):
    return f"SELECT * " \
        f"FROM {table}" \
        f" {build_where( filters,search,  search_fields if len(search_fields)> 0 else deafult_search_columns[table]) }" \
        f"ORDER BY {ordering['order_by']} {ordering['order_direction'].upper()}, id ASC " \
        f"LIMIT {pagination['page_size']} OFFSET {pagination['page_size'] * pagination['page']}"

def build_simple_count(table: str, search, search_fields, filters: dict = {"fixeds": [], "lists": [], "ranges": []}):
    return f"SELECT COUNT(*) " \
        f"FROM {table}" \
        f" {build_where( filters,search,  search_fields if len(search_fields)> 0 else deafult_search_columns[table]) }" \
            