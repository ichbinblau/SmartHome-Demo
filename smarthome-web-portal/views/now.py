# -*- coding: utf-8 -*-
import json
import datetime
import functools
import logging
import os
from jinja2 import TemplateNotFound
from decimal import Decimal
from utils import util, config
from flask import request, session, redirect, url_for, Blueprint, render_template, jsonify, abort
from DB.api import resource, gateway, sensor_group
from utils.settings import BRILLO_GRP, ALERT_GRP, STATUS_GRP, DATA_GRP
from RestClient.sensor import Sensor
from RestClient.api.iotError import IoTRequestError


now_blueprint = Blueprint('now', __name__, )
logger = logging.getLogger(__name__)


def login_required(func):
    """
    Decorator to check whether user's login
    If not, redirect to login page
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login.login', r=ord(os.urandom(1))))
    return wrapper


def _compose_sensor_data(sensor_type, latest_data, record_key, result_key, result):
    """
    :param sensor_type: the sensor type
    :param latest_data: the latest sensor data record
    :param record_key: the keyword stores the data in table
    :param result_key: the key name in the return data dict
    :param result: the return data dict
    :return:
    """

    val_dict = {
        'uuid': latest_data.get('resource').get('uuid') if latest_data.get('resource') else None,
        'resource_id': latest_data.get('resource').get('id') if latest_data.get('resource')
        else latest_data.get('resource_id'),
        'path': latest_data.get('resource').get('path') if latest_data.get('resource') else None,
        'tag': latest_data.get('resource').get('tag') if latest_data.get('resource') else None,
    }

    # extract group background color
    res_obj = latest_data.get('resource')
    color = None
    if res_obj:
        # print latest_data.get('resource').get('sensor_group')
        if res_obj.get('sensor_group_id'):
            color = sensor_group.get_sensor_group(res_obj.get('sensor_group_id'))
            # use the default color if null
        color = {'color': '#fff', 'name': ''} if not color else color
        val_dict.update(
            {'color': color}
        )

    # decouple the tag field for environmental sensors
    if latest_data.get('resource') and latest_data.get('resource').get('tag'):
        # a pure digit string will be treated as json
        tag = latest_data.get('resource').get('tag')
        if util.is_json(tag) and not tag.strip().lstrip('-').isdigit():
            tag_dict = json.loads(tag)
            val_dict.update({
                "tag": tag_dict.get(sensor_type),
            })

    if isinstance(record_key, dict):
        val_dict.update({
            'value': record_key.get('value'),
        })
    elif isinstance(record_key, list):
        for key in record_key:
            val = latest_data.get(key)
            val_dict.update({
                key: str(val) if isinstance(val, (float, Decimal)) else val,
            })
    elif latest_data.get(record_key) is not None:
        val = latest_data.get(record_key)
        val_dict.update({
            'value': str(val) if isinstance(val, (float, Decimal)) else val,
        })
    else:
        val_dict.update({
            'value': "",
        })

    if result_key == "brillo":
        uuid = latest_data.get('resource').get('uuid')
        if result[result_key].get(uuid) is None:
            result[result_key].update({uuid: {sensor_type: val_dict}})
        else:
            result[result_key][uuid].update({sensor_type: val_dict})
    elif result_key == "generic":
        rid = latest_data.get('resource').get('id')
        if result[result_key].get(rid) is None:
            result[result_key].update({rid: val_dict})
        else:
            result[result_key][rid].update(val_dict)
    else:
        if result[result_key].get(sensor_type) is None:
            result[result_key].update({sensor_type: [val_dict, ]})
        else:
            result[result_key][sensor_type].append(val_dict)


def _get_sensor_data(token_dict):
    res = resource.list_resource(status=1, gateway_id=session['gateway_id'])
    default_token = util.format_datetime(util.get_utc_now() - datetime.timedelta(minutes=1))
    ret = {
        'alert': {},
        'status': {},
        'data': {},
        'brillo': {},
        'generic': {}
    }
    for sensor in res:
        typ = sensor.get('sensor_type').get('mapping_class')
        href = sensor.get('path')
        resource_id = sensor.get("id")
        if href.startswith("/brillo/"):
            latest_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format(typ))(
                resource_id=resource_id)
            # print latest_data
            if latest_data is None:
                uuid = sensor.get('uuid')
                if ret['brillo'].get(uuid) is None:
                    ret['brillo'].update({uuid: {typ: {'resource_id': resource_id}}})
                else:
                    ret['brillo'][uuid].update({typ: {'resource_id': resource_id}})
                continue
            if typ in BRILLO_GRP:
                if typ in ['brightness']:
                    keys = [typ]
                elif typ == 'rgbled':
                    keys = ['rgbvalue']
                elif typ == 'audio':
                    keys = ['volume', 'mute']
                elif typ == 'mp3player':
                    keys = ['media_states', 'playlist', 'state', 'title']

                _compose_sensor_data(typ, latest_data, keys, 'brillo', ret)
        else:
            if typ in ALERT_GRP:
                token = token_dict.get(str(resource_id)) if str(resource_id) in token_dict.keys() \
                                                            and token_dict.get(str(resource_id)) else default_token
                latest_data = util.get_class("DB.api.{}.get_latest_alert_by_gateway_uuid"
                                             .format(typ))(resource_id=resource_id,
                                                           token=token)
                latest_data = latest_data if latest_data else {"resource_id": resource_id}
            elif typ == 'power':
                latest_data = util.get_class("DB.api.energy.get_latest_by_gateway_uuid".format(typ))(resource_id=resource_id)
            else:
                latest_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format(typ))(resource_id=resource_id)
            if typ == 'buzzer':
                status_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format(typ))(resource_id=resource_id)
            if latest_data is None:
                continue
            # print latest_data
            if typ in ALERT_GRP:
                _compose_sensor_data(typ, latest_data, 'created_at', 'alert', ret)

            if typ in STATUS_GRP:
                if typ == "rgbled":
                    val = True if latest_data.get('rgbvalue') == "[255, 0, 0]" else False
                    _compose_sensor_data(typ, latest_data, {'value': val}, 'status', ret)
                elif typ == 'buzzer':
                    _compose_sensor_data(typ, status_data, 'status', 'status', ret)
                else:
                    _compose_sensor_data(typ, latest_data, 'status', 'status', ret)
            elif typ in DATA_GRP:
                # extract values from the db query result
                if typ in ['temperature', 'illuminance']:
                    key_words = [typ]
                elif typ == 'solar':
                    key_words = ['tiltpercentage']
                elif typ == 'power':
                    key_words = ['value']
                elif typ == 'environment':
                    key_words = ['temperature', 'humidity', 'pressure', 'uv_index']

                for key in key_words:
                    sensor_type = typ if typ != "environment" else key
                    _compose_sensor_data(sensor_type, latest_data, key, 'data', ret)
            elif typ == "generic":
                _compose_sensor_data(typ, latest_data, 'json_data', 'generic', ret)
    return ret


@now_blueprint.route('/get_sensor')
@login_required
def get_sensor():
    """
    Get sensor data by token
    """
    token_header = request.headers.get('token')
    token_dict = json.loads(token_header) if token_header else dict()
    ret = _get_sensor_data(token_dict)
    return jsonify(data=ret), 201


def _compose_sensor_tag(data):
    if "tag" in data["value"]:
        res = resource.get_resource(id=data["resource_id"])
        sensor_type = res.get("sensor_type").get("mapping_class")

        if sensor_type == "environment":
            new_tag = data["value"]['tag']
            tag = res.get("tag")
            sensor_type = data["type"]
            if sensor_type:
                sensor_type = sensor_type.replace(" ", "_")
            try:
                tag_dict = json.loads(tag)
            except:
                tag_dict = {}
            tag_dict.update({
                sensor_type: new_tag
            })
            data["value"].update({
                "tag": json.dumps(tag_dict)
            })


@now_blueprint.route('/update_sensor_attr', methods=['POST'])
@login_required
def update_sensor_attr():
    """
    Update sensor properties
    :return: uuid and status code
    """
    data = request.json
    logger.debug(data)
    if "resource_id" not in data.keys() \
            or "value" not in data.keys() \
            or not data.get("resource_id") \
            or not data.get("value") \
            or not isinstance(data.get("value"), dict):
        abort(400)
    _compose_sensor_tag(data)
    updated_res = resource.update_resource(id=data['resource_id'], **data["value"])
    return jsonify(resource_id=updated_res.get("id")), 200


@now_blueprint.route('/get_geo_location')
@login_required
def get_geo_location():
    """Get the Geolocation of the current account"""
    location = gateway.get_gateway(gateway_id=session.get('gateway_id'))
    # remove unnecessary keys
    location.pop('url', None)
    return jsonify({'geo': location}), 201


@now_blueprint.route('/update_sensor', methods=['PUT'])
@login_required
def update_sensor():
    """
    update sensor status
    Http PUT: {
                'resource_id': '5',
                'data': { 'value': false}
                }
    """
    content = request.get_json(silent=True)
    resource_id = content.get('resource_id')
    data = content.get('data')
    if not resource_id or not isinstance(resource_id, int):
        abort(400)
    try:
        res = resource.get_resource(id=resource_id)
    except:
        abort(404)
    logger.info("content: " + str(content))
    sensor = Sensor(uuid=res.get('uuid'), path=res.get('path'), gateway_id=session.get('gateway_id'))
    try:
        sts = sensor.update_status(data)
        return jsonify({'status': sts}), 201
    except IoTRequestError:
        abort(500)


@now_blueprint.route('/add_sensor_group', methods=['POST'])
@login_required
def add_sensor_group():
    """
    update sensor group
    Http POST: {
                'gateway_id': 1,
                'color': '#fff',
                'name': 'name',
                }
    """
    content = request.get_json(silent=True)
    gateway_id = content.get('gateway_id')
    if not gateway_id or not content.get('color') or not content.get('name'):
        abort(400)
    if not isinstance(gateway_id, int):
        if not isinstance(gateway_id, str):
            abort(400)
        elif not gateway_id.isdigit():
            abort(400)
    try:
        return jsonify(sensor_group.new(content)), 201
    except:
        abort(500)


@now_blueprint.route('/cf_instance')
@login_required
def get_instance():
    """
    Get instance ID and total running instances in the CF Cloud
    Return data in json format
    Not implemented yet for k8s
    """
    inst = {}
    return jsonify({'cf_instance': inst}), 201


@now_blueprint.route('/get_groups')
@login_required
def list_sensor_groups():
    """
    Get the sensor groups of the current gateway
    Return data in json format
    """
    gateway_id = session['gateway_id']
    sg = sensor_group.get_all_groups(gateway_id=gateway_id)
    return jsonify(sensor_groups=sg)


@now_blueprint.route('/get_gateways')
def list_gateways():
    # todo: need some security mechanism to protect the data
    # list all registered gateways
    gateways = gateway.list_gateways()

    keyword = config.get_map_keyword()
    types = config.get_map_types()
    return jsonify({'gateways': gateways,
                    'keyword': keyword,
                    'types': types}), 201


@now_blueprint.route('/')
def root():
    try:
        return redirect(url_for('login.login'), code=302)
    except TemplateNotFound:
        abort(404)


@now_blueprint.route('/index')
@login_required
def index():
    try:
        return render_template('home_dashboard.html', static_url_prefix="")
    except TemplateNotFound:
        abort(404)
