import re


def camel_to_snake(text: str) -> str:
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()


def format_filters(fixeds):
    filters = {}
    for filter in fixeds:
        filters[filter['key']] = filter['value']
    return filters


def format_common_search(common_search):
    return {
        "pagination": {"page": common_search['page'],
                       "page_size": common_search['page_size']},
        "ordering": {
            "order_by": common_search['order_by'],
            "order_direction": common_search['order_direction']
        },
        "filters": {
            "fixeds": format_filters(common_search['filters']['fixeds']),
            "lists": format_filters(common_search['filters']['lists']),
            "ranges": format_filters(common_search['filters']['ranges']),
        },
        "search": common_search['search'],
        "search_fields": common_search['search_fields']
    }
