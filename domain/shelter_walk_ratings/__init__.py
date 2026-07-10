import repository.shelter_walk_ratings as shelter_walk_ratings_data
import domain.shelter_walks as shelter_walks_domain
from utils.logger import logger, stringify


# --- field resolvers ---
def get_shelter_walk(obj, info):
    return shelter_walks_domain.get_shelter_walk(obj['walk_id'])


def get_ratings_for_shelter_walk(obj, info):
    return shelter_walk_ratings_data.get_ratings_by_walk(obj['id'])


# --- business ---
def create_shelter_walk_rating(data):
    logger.domain(f'data: {stringify(data)}')
    try:
        return shelter_walk_ratings_data.create_shelter_walk_rating(data)
    except Exception as e:
        logger.error(e)
        raise e
