# -*- coding: utf-8 -*-
"""
Pull forecast and historical weather
and do power usage prediction by weather
"""
import requests
import json
import copy
from datetime import datetime
from datetime import timedelta

from config import FORECAST_URL, HISTORICAL_URL, FORECAST_RANGE, PROXY
#from admin import db
from admin.models import db, ActualWeather, HisWeather, PredictedPower, ActualPower
from admin.machine_learning import predict
from pprint import pprint
from utils import gen_randint


def http_get(url, params=None):
    ret = requests.get(url, params=params, verify=False, proxies=PROXY)
    ret.raise_for_status()
    pprint(ret.url)
    return ret.content


def get_avg_temp(high, low):
    avg_temp = (float(high) + float(low)) / 2
    return avg_temp


def get_temp_forecast(geo_location, gateway_id):
    geo = "({})".format(",".join(geo_location))
    yql_query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + geo + "')"
    params = {
        'q': yql_query,
        'format': 'json'
    }
    result = http_get(FORECAST_URL, params)
    data = json.loads(result)

    # the query date
    today = data['query']['results']['channel']['item']['pubDate'].rsplit(" ", 1)[0]
    publish_date = datetime.strptime(today, '%a, %d %b %Y %I:%M %p').date()

    # forecast for the coming 3 days
    forecast = data['query']['results']['channel']['item']['forecast']

    # today's weather
    temp_0 = ""
    f_list = list()

    for i in range(0, FORECAST_RANGE + 1):
        temp = get_avg_temp(forecast[i]['high'], forecast[i]['low'])
        if i == 0:
            temp_0 = temp
        d_temp_forecast = dict()
        d_temp_forecast['publish_date'] = publish_date + timedelta(days=i)
        d_temp_forecast['forecast_date'] = publish_date
        d_temp_forecast['temperature'] = temp
        d_temp_forecast['order'] = 24 * i
        d_temp_forecast['region_id'] = gateway_id
        f_list.append(d_temp_forecast)

    pprint(f_list)
    return publish_date, f_list, temp_0


def get_temp_his_value(geo_location, date_str):
    geo = ",".join(geo_location)
    yql_url = HISTORICAL_URL + "history_" + date_str + "/q/" + geo + ".json"
    result = http_get(yql_url)
    data = json.loads(result)
    return data['history']['dailysummary'][0]['meantempi']


def get_temp_his(geo, today, gateway_id, temp_0):
    temp_list = []
    temp_list.append({
        'publish_date': today,
        'temperature': temp_0,
        'region_id': gateway_id
    })
    for i in range(1, FORECAST_RANGE + 1):
        his_date = today + timedelta(days=-1*i)
        d_temp_his = dict()
        d_temp_his['publish_date'] = his_date
        d_temp_his['temperature'] = get_temp_his_value(geo, datetime.strftime(his_date, '%Y%m%d'))
        d_temp_his['region_id'] = gateway_id
        temp_list.append(d_temp_his)
    pprint(temp_list)
    return temp_list


def predict_forecast(model_name, temp_forecast_list, publish_date):
    predict_forecast_list = []
    order = 0
    for i, v in enumerate(temp_forecast_list):
        if v['publish_date'] == publish_date:
            continue
        d_predict_forecast = {}
        r_value = predict.predict(model_name, 2, int(v['temperature']))
        d_predict_forecast['publish_date'] = v['publish_date']
        d_predict_forecast['region_id'] = v['region_id']
        d_predict_forecast['predict_date'] = publish_date
        d_predict_forecast['order'] = order
        d_predict_forecast['power'] = r_value
        predict_forecast_list.append(d_predict_forecast)
    return predict_forecast_list


def predict_his(model_name, temp_his_list):
    predict_his_list = []
    for i, v in enumerate(temp_his_list):
        d_predict_his = {}
        r_value = predict.predict(model_name, 2, int(v['temperature']))
        d_predict_his['collect_date'] = v['publish_date']
        d_predict_his['region_id'] = v['region_id']
        d_predict_his['power'] = r_value
        predict_his_list.append(d_predict_his)
    # print predict_his_list
    return predict_his_list


def bulk_insert(klass, data):
    try:
        for i, v in enumerate(data):
            dm = klass(**v)
            db.session.add(dm)
            db.session.flush()
        db.session.commit()
    except Exception as e:
        print e.message
        db.session.rollback()
        db.session.remove()


def set_temp_forecast(list_temp_forecast):
    bulk_insert(ActualWeather, list_temp_forecast)


def set_temp_his(list_temp_his):
    bulk_insert(HisWeather, list_temp_his)


def set_predict_forecast(list_predict_forecast):
    bulk_insert(PredictedPower, list_predict_forecast)


def set_predict_his(list_predict_his, publish_date):
    for i, v in enumerate(list_predict_his):
        v['predict_date'] = publish_date
        v['publish_date'] = v['collect_date']
        v['order'] = 0
        v.pop('collect_date', None)
    bulk_insert(PredictedPower, list_predict_his)


def set_actual_his(list_predict_his):
    actual_his = copy.deepcopy(list_predict_his)

    for i, v in enumerate(actual_his):
        if i != 0:
            actual_his[i]['power'] = float(v['power']) + gen_randint(-2, 2)
    bulk_insert(ActualPower, actual_his)


if __name__ == "__main__":
    geo = ('32.714987', '-117.167359')
    publish_date, list_temp_forecast, today_temp = get_temp_forecast(geo, 1)
    list_temp_his = get_temp_his(geo, publish_date, 1, today_temp)
    # print list_temp_his
    # set_temp_his(list_temp_his)
    # set_temp_forecast(list_temp_forecast)
    model_name = 'sh-model'
    list_predict_forecast = predict_forecast(model_name, list_temp_forecast, publish_date)
    list_predict_his = predict_his(model_name, list_temp_his)
    pprint(list_predict_forecast)
    pprint(list_predict_his)
    # set_actual_his(list_predict_his)
    # set_predict_his(list_predict_his, publish_date)
    # set_predict_forecast(list_predict_forecast)
