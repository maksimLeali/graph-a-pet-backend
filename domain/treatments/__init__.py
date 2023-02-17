from api.errors import NotFoundError
from ariadne import convert_kwargs_to_snake_case
import repository.treatments as treatments_data
from repository.treatments.models import FrequencyUnit
import domain.health_cards as health_cards_domain
from utils.logger import logger, stringify
from utils import format_common_search
from math import ceil
import pydash as py_
import pendulum as pdl


def setUnits(frequency_unit, value):
    years, months, weeks, days = 0, 0, 0, 0
    if (frequency_unit == FrequencyUnit.YEARLY.name):
        years = value
    elif (frequency_unit == FrequencyUnit.MONTHLY.name):
        months = value
    elif (frequency_unit == FrequencyUnit.WEEKLY.name):
        weeks = value
    elif (frequency_unit == FrequencyUnit.DAILY.name):
        days = value
    return years, months, weeks, days


def get_health_card(health_card_id):
    try:
        return health_cards_domain.get_health_card(health_card_id)
    except Exception as e:
        logger.error(e)
        raise e


def get_paginated_treatments(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        pagination = get_pagination(common_search)
        treatments = get_treatments(common_search)
        logger.check(f"pagination: {stringify(pagination)}")
        return (treatments, pagination)
    except Exception as e:
        logger.error(e)
        raise e


def create_treatment(data, props_booster_id=None):
    logger.domain(
        f"treatment: {stringify(data)}\n"
        f"id: {props_booster_id}"
    )
    try:
        if(data.get('booster_date') is not None):
            booster = create_treatment(py_.omit({
                **data,
                'date': data['booster_date']
            },
                'booster_date'))
            data = py_.omit(data, 'booster_date')
            props_booster_id = booster['id']

        if(not None in [data.get('frequency_times'), data.get('frequency_value'), data.get('frequency_unit')]):
            years, months, weeks, days = setUnits(
                data['frequency_unit'], data['frequency_value'])
            for i in range(1, data['frequency_times']):
                new_date = pdl.parse(data['date']).add(years=years * (data['frequency_times'] - i), months=months * (
                    data['frequency_times'] - i), weeks=weeks * (data['frequency_times'] - i), days=days * (data['frequency_times'] - i))
                temp_booster = create_treatment(py_.omit({
                    **data,
                    "date": str(new_date).replace('+00:00', 'Z'),
                    "booster_id": props_booster_id,
                },
                    ['frequency_value', 'frequency_unit', 'frequency_times']
                ), props_booster_id)
                props_booster_id = temp_booster['id']
        data['booster_id'] = props_booster_id
        treatment = treatments_data.create_treatment(data)
        logger.check(f"Treatment : {stringify(data)}")
        return treatment
    except Exception as e:
        logger.error(e)
        raise e


def update_treatment(id, data):
    logger.domain(
        f"id: {id}\n"
        f"data: {data}"
    )
    try:
        treatment = get_treatment(id)
        if(treatment.get('booster_id') != None) :
            booster = get_treatment(treatment.get('booster_id'))
        if (data.get('booster_date') != None):
            try:
                booster = get_treatment(treatment['booster_id'])
                new_booster_date = data['booster_date']
                treatments_data.update_treatment(booster['id'], {
                    **py_.omit(data, ['frequency_unit',
                                      'frequency_time',
                                      'frequency_value',
                                      'booster_date']), "date": new_booster_date
                })
            except NotFoundError as e:
                booster = create_treatment(py_.omit(
                    {**treatment, **data}, ['frequency_unit', 'frequency_time', 'frequency_value', 'booster_date']))
            except Exception as e:
                logger.error(e)
                raise e
            
        if(not None in [data.get('frequency_times'), data.get('frequency_value'), data.get('frequency_unit')] and booster != None):
            delete_boosters(booster)
            years, months, weeks, days = setUnits(
                data['frequency_unit'], data['frequency_value'])
            update_booster_id = None
            for i in range(1, data['frequency_times']):
                new_date = pdl.parse(treatment['date']).add(years=years * (data['frequency_times'] - i), months=months * (
                    data['frequency_times'] - i), weeks=weeks * (data['frequency_times'] - i), days=days * (data['frequency_times'] - i))
                logger.info(new_date)
                temp_booster = create_treatment(py_.omit({
                    **treatment,
                    **data,
                    "date": str(new_date).replace('+00:00', 'Z'),
                    "booster_id": update_booster_id,
                },
                    ['frequency_value', 'frequency_unit', 'frequency_times']
                ), update_booster_id)
                update_booster_id = temp_booster['id']
                booster = temp_booster
            pass
        if (len(py_.omit(data, 'booster_date').keys()) > 0 or booster != None):
            treatment = treatments_data.update_treatment(id, py_.omit(
                {**data, "booster_id": booster['id'] if booster != None else None}, 'booster_date'))
        logger.check(f"treatment {stringify(treatment)}")
        return treatment
    except Exception as e:
        logger.error(e)
        raise e

def delete_boosters(treatment):
    booster_id = treatment.get('booster_id')
    if booster_id != None:
        booster = get_treatment(booster_id)
        delete_boosters(booster)
    logger.check(f'end: {booster_id} ')
    treatments_data.delete_treatment(treatment['id'])
    


def get_treatments(common_search):
    logger.domain(f"common_search: {stringify(common_search)}")
    try:
        treatments = treatments_data.get_treatments(common_search)
        logger.check(f"treatments: {len(treatments)}")
        return treatments
    except Exception as e:
        logger.error(e)
        raise e


def get_treatment(id):
    logger.domain(f"id: {id}")
    try:
        return treatments_data.get_treatment(id)
    except Exception as e:
        logger.error(e)
        raise e


def get_pagination(common_search):
    try:
        total_items = treatments_data.get_total_items(common_search)
        page_size = common_search['pagination']['page_size']
        total_pages = ceil(total_items / page_size)
        current_page = common_search['pagination']['page']
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(e)
        raise Exception(e)
