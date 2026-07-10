import repository.pet_weights as pet_weights_data
import domain.pets as pets_domain
from domain.period_buckets import parse_dt, bucket_key, labels_for_period
from utils.logger import logger, stringify


def create_pet_weight(data):
    logger.domain(f"data: {stringify(data)}")
    try:
        weight = pet_weights_data.create_pet_weight(data)
        # keep the pet's current-weight snapshot (pets.weight_kg) in sync
        pets_domain.update_pet(data["pet_id"], {"weight_kg": data["weight_kg"]})
        return weight
    except Exception as e:
        logger.error(e)
        raise e


def get_latest_weight(pet_id):
    logger.domain(f"pet_id: {pet_id}")
    try:
        return pet_weights_data.get_latest_weight(pet_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_pet_weight_stats(pet_id, period):
    logger.domain(f"pet_id: {pet_id} period: {period}")
    try:
        rows = pet_weights_data.get_weights_by_pet(pet_id)
        labels = labels_for_period(period)
        label_index = {label: i for i, label in enumerate(labels)}
        acc = {}  # label -> [sum, count]
        for r in rows:
            label = bucket_key(parse_dt(r["created_at"]), period)
            if label not in label_index:
                continue
            cur = acc.setdefault(label, [0, 0])
            cur[0] += r["weight_kg"]
            cur[1] += 1
        data = []
        for label in labels:
            cur = acc.get(label)
            data.append(round(cur[0] / cur[1], 2) if cur else None)
        return {"labels": labels, "data": data}
    except Exception as e:
        logger.error(e)
        raise e
