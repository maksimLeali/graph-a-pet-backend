from math import ceil
import pydash as py_

import repository.walk_ratings as walk_ratings_data
import domain.walks as walks_domain
import domain.damnationes_memoriae as damnatio_domain
from utils.logger import logger, stringify


def get_walk(obj, info):
    return walks_domain.get_walk(obj['walk_id'])


def create_walk_rating(data):
    logger.domain(f'data: {stringify(data)}')
    try:
        walk_rating = walk_ratings_data.create_walk_rating(data)
        return walk_rating
    except Exception as e:
        logger.error(e)
        raise e


def update_walk_rating(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {stringify(data)}"
    )
    try:
        walk_rating = walk_ratings_data.update_walk_rating(
            id, py_.pick(data, ["type", "rating"]))
        logger.check(f"walk_rating: {stringify(walk_rating)}")
        return walk_rating
    except Exception as e:
        logger.error(e)
        raise e


def delete_walk_rating(id, user_id):
    logger.domain(f"id {id} remove ")
    try:
        walk_rating = walk_ratings_data.get_walk_rating(id)
        damnatio_id = damnatio_domain.delete_row(
            id, 'walk_ratings', walk_rating, user_id)
        return damnatio_id
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_walk_ratings(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        walk_ratings = get_walk_ratings(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (walk_ratings, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def get_walk_ratings(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        walk_ratings = walk_ratings_data.get_walk_ratings(common_search)
        logger.output(f"walk_ratings: {len(walk_ratings)}")
        return walk_ratings
    except Exception as e:
        logger.error(e)
        raise e


def get_walk_rating(id):
    logger.domain(f"id: {id}")
    try:
        walk_rating = walk_ratings_data.get_walk_rating(id)
        logger.check(f"walk_rating: {stringify(walk_rating)}")
        return walk_rating
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    logger.input(f"common_search: {stringify(common_search)}")
    try:
        total_items = walk_ratings_data.get_total_items(common_search)
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
