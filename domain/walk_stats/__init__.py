from repository.walk_ratings.models import WalkRatingType
import repository.walk_ratings as walk_ratings_data
import repository.shelter_walk_ratings as shelter_walk_ratings_data
from domain.period_buckets import parse_dt, bucket_key, labels_for_period
from utils.logger import logger


def _build_chart(rows, period):
    """rows: iterable of dicts with created_at/type/rating (as returned by
    the *_ratings repositories' to_dict()). Buckets by period into a
    chart.js-ready {labels, series} shape (null where a (period, type) has
    no ratings, so the line renders a gap instead of dropping to 0)."""
    labels = labels_for_period(period)
    label_index = {label: i for i, label in enumerate(labels)}
    acc = {}  # (label, type) -> [sum, count]
    for r in rows:
        if not r.get("type") or r.get("rating") is None:
            continue
        label = bucket_key(parse_dt(r["created_at"]), period)
        if label not in label_index:
            continue
        key = (label, r["type"])
        cur = acc.setdefault(key, [0, 0])
        cur[0] += r["rating"]
        cur[1] += 1

    series = []
    for t in WalkRatingType:
        data = []
        for label in labels:
            cur = acc.get((label, t.name))
            data.append(round(cur[0] / cur[1], 2) if cur else None)
        series.append({"type": t.name, "data": data})

    return {"labels": labels, "series": series}


def get_pet_walking_stats(pet_id, period):
    logger.domain(f"pet_id: {pet_id} period: {period}")
    try:
        rows = walk_ratings_data.get_ratings_by_pet(pet_id)
        return _build_chart(rows, period)
    except Exception as e:
        logger.error(e)
        raise e


def get_shelter_pet_walking_stats(shelter_pet_id, period):
    logger.domain(f"shelter_pet_id: {shelter_pet_id} period: {period}")
    try:
        rows = shelter_walk_ratings_data.get_ratings_by_shelter_pet(shelter_pet_id)
        return _build_chart(rows, period)
    except Exception as e:
        logger.error(e)
        raise e
