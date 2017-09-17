# -*- coding: utf-8 -*-
import json
import logging
from flask import session, render_template, request, Blueprint, abort
from . import login_required
from admin import weather_api
from admin.models import db, Gateway, GatewayModel, DataModel, _wrapper_dict

gw_model_bp = Blueprint('gw_model', __name__)
logger = logging.getLogger(__name__)


@gw_model_bp.route('/load_weather/', methods=['GET'])
@login_required
def load_weather():
    obj = Gateway.query.all()
    gws = _wrapper_dict(obj, ['id', 'name', 'url', 'address', 'latitude', 'longitude', 'created_at'])
    gw_model = GatewayModel.query.order_by(GatewayModel.id).all()
    ret = _wrapper_dict(gw_model, ['id', 'gateway_id', 'model_id'])
    mapping = {row['gateway_id']: row['model_id'] for row in ret}
    # print mapping
    dm = DataModel.query.all()
    models = _wrapper_dict(dm, ['id', 'name'])
    return render_template('load.html', username=session.get('username'), gateways=gws, mapping=mapping, models=models)


@gw_model_bp.route('/load', methods=['PUT'])
@login_required
def load_data():
    content = request.get_json(silent=True)
    geo = content.get('geo')
    gw_id = content.get('gw_id')
    # model_name = content.get('model_name')
    resp = {}
    ret_code = 200
    if not geo or not gw_id:
        abort(400)
    gm = db.session.query(GatewayModel).filter(GatewayModel.gateway_id == gw_id).all()
    if gm:
        try:
            gm_dict = _wrapper_dict(gm, ["data_model"])
            print gm_dict
            model_name = gm_dict[0]["data_model"]["name"]
            publish_date, list_temp_forecast, today_temp = weather_api.get_temp_forecast(geo, gw_id)
            list_temp_his = weather_api.get_temp_his(geo, publish_date, gw_id, today_temp)
            weather_api.set_temp_his(list_temp_his)
            weather_api.set_temp_forecast(list_temp_forecast)
            list_predict_forecast = weather_api.predict_forecast(model_name, list_temp_forecast, publish_date)
            list_predict_his = weather_api.predict_his(model_name, list_temp_his)
            weather_api.set_actual_his(list_predict_his)
            weather_api.set_predict_his(list_predict_his, publish_date)
            weather_api.set_predict_forecast(list_predict_forecast)
        except Exception as e:
            resp['error'] = e.message
            ret_code = 500
    else:
        resp['error'] = "The gateway is not bound with any models."
        ret_code = 400
    return json.dumps(resp), ret_code


@gw_model_bp.route('/gateway_model', methods=['PUT', 'POST'])
@login_required
def gateway_model():
    content = request.get_json(silent=True)
    gw_id = content.get('gateway_id')
    model_id = content.get('model_id')
    resp = {}
    ret_code = 200
    print content
    if request.method == 'POST':
        # insert new
        if not gw_id or not model_id:
            abort(400)
        data = {"gateway_id": gw_id, "model_id": model_id}
        try:
            GatewayModel.create(**data)
        except Exception as e:
            resp['error'] = e.message
            ret_code = 500
    elif request.method == 'PUT':
        # delete
        try:
            gm = db.session.query(GatewayModel).\
                filter(GatewayModel.model_id == model_id, GatewayModel.gateway_id == gw_id).one()
            if gm:
                gm.delete()
        except Exception as e:
            resp['error'] = e.message
            ret_code = 500
    return json.dumps(resp), ret_code
