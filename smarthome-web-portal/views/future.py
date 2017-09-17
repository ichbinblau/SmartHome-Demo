# -*- coding: utf-8 -*-
import datetime
import json
import os
import logging
from pprint import pprint
from datetime import timedelta
from flask import session
from flask.ext.socketio import emit
from . import socketio
from DB.api import actual_weather, actual_power, his_weather, predicted_power, gateway_model

logger = logging.getLogger(__name__)


@socketio.on('my temp', namespace='/index')
def get_temp(message):
    today_date_str = message.get('today_date')
    data, error = None, None
    logger.debug(today_date_str)

    try:
        today_date = datetime.datetime.strptime(today_date_str, "%m/%d/%Y").date()
    except ValueError:
        error = "Invalid date format: " + today_date_str

    start_date = today_date - timedelta(days=3)
    end_date = today_date + timedelta(days=3)
    logger.debug(start_date, end_date)

    actual = temp_actual(start_date, today_date)
    future = temp_future(today_date, end_date)
    if not actual or not future:
        error = "Incomplete data. Plz load weather data in admin portal."
    else:
        data = {
            "actual": actual,
            "future": future
        }

    if data:
        emit('my temp resp', {'data': data})
    else:
        emit('my temp resp', {'error': error})


def temp_actual(start, end):
    logger.debug("######temp_actual#######")
    max_date = his_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(end))
    if not max_date:
        return []
    his_weather_info = his_weather.get_weather_by_date(start, end, region_id=session.get('gateway_id'),
                                                       created_at={'ge': str(max_date[0][0])},
                                                       order_by=[('publish_date', False)])
    logger.debug(his_weather_info)

    # convert the date object to string
    for info in his_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
    return his_weather_info


def temp_future(start, end):
    logger.debug("######temp_future#######")
    max_date = actual_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(start))
    if not max_date:
        return []
    actual_weather_info = actual_weather.get_weather_by_date(start, end, region_id=session.get('gateway_id'),
                                                             created_at={'ge': str(max_date[0][0])},
                                                             order_by=[('publish_date', False)])
    logger.debug(actual_weather_info)
    for info in actual_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
        info['forecast_date'] = info['forecast_date'].strftime('%Y-%m-%d')
    return actual_weather_info


def temp_today(start, end):
    logger.debug("######temp_today#####")
    max_date = actual_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(start))
    if not max_date:
        return []
    actual_weather_info = actual_weather.get_weather_by_date(start, end, order=0, region_id=session.get('gateway_id'),
                                                             created_at={'ge': str(max_date[0][0])},
                                                             order_by=[('publish_date', False)])
    logger.debug(actual_weather_info)
    for info in actual_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
        info['forecast_date'] = info['forecast_date'].strftime('%Y-%m-%d')
    return actual_weather_info


@socketio.on('my power', namespace='/index')
def get_power(message):
    today_date_str = message.get('today_date')
    data, error = None, None
    logger.debug(today_date_str)

    try:
        today_date = datetime.datetime.strptime(today_date_str, "%m/%d/%Y").date()
    except ValueError:
        error = "Invalid date format: " + today_date_str

    start_date = today_date - timedelta(days=3)
    end_date = today_date + timedelta(days=3)
    logger.debug(start_date, end_date)

    actual = power_actual(start_date, today_date)
    predict = power_predict_his(start_date, end_date, today_date)
    # future = power_future(today_date, end_date)
    if not actual or not predict:
        error = "Incomplete data. Plz load data in admin portal. "
    else:
        data = {
            "actual": actual,
            "future": predict[3:],
            'predict_his': predict[:4]
        }
    if data:
        emit('my power resp', {'data': data})
    else:
        emit('my power resp', {'error': error})


def power_actual(start_date, end_date):
    logger.debug("######power_actual#######")
    max_date = actual_power.get_max_date(gateway_id=session.get('gateway_id'), collect_date=str(end_date))
    if not max_date:
        return []
    actual_power_info = actual_power.get_power_by_date(start_date, end_date, region_id=session.get('gateway_id'),
                                                       created_at={'ge': str(max_date[0][0])},
                                                       order_by=[('collect_date', False)])
    for info in actual_power_info:
        info['collect_date'] = info['collect_date'].strftime('%Y-%m-%d')
    pprint(actual_power_info)
    return actual_power_info


def power_predict_his(start_date, end_date, today_date):
    logger.debug("#########power_predict#########")
    max_date = predicted_power.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(today_date))
    if not max_date:
        return []
    predict_power_info = predicted_power.get_power_by_date(start_date, end_date, order=0,
                                                           region_id=session.get('gateway_id'),
                                                           created_at={'ge': str(max_date[0][0])},
                                                           order_by=[('publish_date', False)])
    for info in predict_power_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
    return predict_power_info


@socketio.on('my model', namespace='/index')
def get_data_model():
    data_model = gateway_model.get_gateway_model(session.get("gateway_id"))
    admin_uri = None
    env_str = os.getenv("VCAP_APPLICATION", "")
    if data_model:
        if env_str:
            env_dict = json.loads(env_str)
            uris = env_dict.get("application_uris", None)
            if uris:
                admin_uri = uris[0].split(".")
                admin_uri[0] = "smarthome-adminportal"
                admin_uri = ".".join(admin_uri)
        elif os.path.isfile('/.dockerenv'):
            admin_uri = "image/model/"
        else:
            admin_uri = "http://localhost:4000/images/model/"
    emit('my model resp', admin_uri + data_model['data_model']['name'] + ".png" if data_model and admin_uri else data_model)
