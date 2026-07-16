from ariadne import convert_kwargs_to_snake_case
import domain.shelter_walk_ratings as shelter_walk_ratings_domain
import domain.shelter_walks as shelter_walks_domain
from api.middlewares import auth_middleware
from api.shelter_walks.mutations import assert_staff_or_own_walk
from api.errors import format_error
from utils.logger import logger, stringify


@convert_kwargs_to_snake_case
@auth_middleware
def create_shelter_walk_rating_resolver(obj, info, data):
    logger.api(f"data: {stringify(data)}")
    try:
        token = info.context.headers['authorization']
        # STAFF+ o volontario sulla propria walk
        assert_staff_or_own_walk(token, data["walk_id"])
        walk_rating = shelter_walk_ratings_domain.create_shelter_walk_rating(data)
        return {"success": True, "walk_rating": walk_rating}
    except Exception as e:
        logger.error(e)
        return {
            "success": False,
            "error": format_error(e, info.context.headers['authorization']),
        }
