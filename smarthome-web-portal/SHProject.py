# -*- coding: utf-8 -*-
"""
app view
"""
import os
import json
import logging
import hashlib
import functools
from pprint import pprint
import datetime
from flask import redirect, url_for, abort
from flask import request, session, make_response
from flask import Flask, render_template, jsonify
from flask.ext.socketio import SocketIO, emit, disconnect
from decimal import Decimal
from utils import logsettings
from utils import util
from utils.config import config
from DB.api import resource, user, gateway, sensor_group, actual_weather, actual_power, his_weather, predicted_power, \
    gateway_model, activity
from RestClient.sensor import Sensor
from RestClient.api import ApiClient
from RestClient.api.iotError import IoTRequestError
from utils.settings import SECRET_KEY, ALERT_GRP, STATUS_GRP, DATA_GRP, BRILLO_GRP
from datetime import timedelta

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

""" static resource location"""
static_url_prefix = ''
app = Flask(__name__, static_url_path='')

app.config['SECRET_KEY'] = SECRET_KEY

logger = logging.getLogger(__name__)
socketio = SocketIO(app, pingTimeout=60)


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
            return redirect(url_for('login'))
    return wrapper


def authenticated_only(f):
    """
    Check login for web socket connections
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


def _get_historical_data(sensor, start_time, end_time, res_list=[]):
    try:
        if not res_list:
            return []
        get_data = util.get_class("DB.api.{}.get_data_by_time".format(sensor))
        dic = get_data(start_time, end_time, res_list)
        # print dic
        return [] if not dic else dic
    except ImportError:
        abort(400)


@socketio.on('my data', namespace='/index')
def get_historical_data(message):
    """
    Get average sensor data in a period of time
    """
    sensor = message['sensor']
    date_range = message['date_range']
    gateway_id = session['gateway_id']
    print sensor, date_range, gateway_id
    res_list = resource.list_resource(gateway_id=gateway_id)
    res_id = [res['id'] for res in res_list if res['sensor_type']['mapping_class'] == sensor]

    data = []
    if res_id:
        start_time = date_range[0]
        end_time = date_range[1]
        data = _get_historical_data(sensor, start_time, end_time, res_id)

    print res_id, data
    emit('my ' + sensor, {'data': data})


@socketio.on('connect', namespace='/index')
@authenticated_only
def on_connect():
    logger.info('Connected.')
    emit('my response', {'data': 'User “{0}” has joined.'.format(session['username'])})


@socketio.on('disconnect', namespace='/index')
def on_disconnect():
    logger.info('Client disconnected')


@socketio.on_error('/index')  # handles the '/index' namespace
def error_handler_index(e):
    logger.info(e.message)


def _compose_sensor_data(sensor_type, latest_data, record_key, result_key, result):
    """
    :param sensor_type: the sensor type
    :param latest_data: the latest sensor data record
    :param record_key: the keyword stores the data in table
    :param result_key: the key name in the return data dict
    :param result: the return data dict
    :return:
    """
    val_dict = {}
    if latest_data:
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
        val_dict.update(record_key)
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
    elif result_key == "activity":
        uuid = latest_data.get('resource').get('uuid')
        result[result_key].update({uuid: val_dict})
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
        'generic': {},
        'activity': {},
    }

    motion_led_list = []

    # todo: to be removed
    # led_list = [3, 6]
    for sensor in res:
        typ = sensor.get('sensor_type').get('mapping_class')
        href = sensor.get('path')
        resource_id = sensor.get("id")
        if href.startswith("/a/"):
            if typ in ALERT_GRP:
                token = token_dict.get(str(resource_id)) if str(resource_id) in token_dict.keys() \
                                                            and token_dict.get(str(resource_id)) else default_token
                latest_data = util.get_class("DB.api.{}.get_latest_alert_by_gateway_uuid"
                                             .format(typ))(resource_id=resource_id,
                                                           token=token)
                latest_data = latest_data if latest_data else {"resource_id": resource_id}
            elif typ == 'power':
                latest_data = util.get_class("DB.api.energy.get_latest_by_gateway_uuid".format(typ))(
                    resource_id=resource_id)
            else:
                latest_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format(typ))(
                    resource_id=resource_id)

            if typ == 'buzzer':
                status_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format(typ))(
                    resource_id=resource_id)

            if latest_data is None:
                continue
            # print latest_data

            # add activity
            if typ == 'motion':

                # 1. pair rgb led with motion
                # uuid = sensor.get("uuid")
                href_id = href.split('-')[-1]
                rgbled_data = None
                print "href id " + href_id

                led_in_pair = [dev.get('id') for dev in res if "-".join(("/a/rgbled", href_id)) in dev.itervalues()
                               and dev.get("sensor_type_id") == 8]
                print "pair id " + str(led_in_pair)
                # todo: to be removed
                # led_in_pair = [led_list.pop()]
                if led_in_pair:
                    rgbled_data = util.get_class("DB.api.{}.get_latest_by_gateway_uuid".format('rgbled'))(
                        resource_id=led_in_pair[0])
                if not rgbled_data:
                    val = rgbled_data
                    rgbled_data = {
                        'resource': {'uuid': sensor.get("uuid")}
                    }
                elif str(rgbled_data.get('rgbvalue')).strip() == "[255, 0, 0]":
                    val = True
                else:
                    val = False

                if rgbled_data:
                    print str(rgbled_data.get('rgbvalue')).strip()

                # 2. get total activities by id
                act = activity.get_activity(resource_id=resource_id)
                total = act.get('total') if act else 0
                _compose_sensor_data(typ, rgbled_data, {'total': total, 'rgb_led': val}, 'activity', ret)

                # 3. record the motion led pairing info
                # print rgbled_data.get("resource")
                if "id" in rgbled_data.get("resource"):
                    motion_led_info = {'activity': total,
                                       'led_id': rgbled_data.get("resource").get("uuid"),
                                       'led_pth': rgbled_data.get("resource").get("path")}

                    motion_led_list.append(motion_led_info)

            if typ in ALERT_GRP:
                _compose_sensor_data(typ, latest_data, 'created_at', 'alert', ret)

            if typ in STATUS_GRP:
                # Remove rgb_led from the status panel
                # if typ == "rgbled":
                #     val = True if latest_data.get('rgbvalue') == "[255, 0, 0]" else False
                #     _compose_sensor_data(typ, latest_data, {'value': val}, 'status', ret)
                if typ == 'buzzer':
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
        elif href.startswith("/brillo/"):
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

    _update_motion_led(motion_led_list)
    return ret


def _update_motion_led(motion_led_list):
    print motion_led_list
    if len(motion_led_list) == 0:
        return
    ma = max([item["activity"] for item in motion_led_list])
    for motion_led in motion_led_list:
        sensor = Sensor(motion_led["led_id"], motion_led["led_pth"], session["gateway_id"])
        if motion_led["activity"] == ma:
            # set red color
            sensor.update_status_async({"rgbValue": [255, 0, 0]})
        else:
            # set blue color
            sensor.update_status_async({"rgbValue": [0, 0, 255]})
            

@app.route('/get_sensor')
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


@app.route('/update_sensor_attr', methods=['POST'])
@login_required
def update_sensor_attr():
    """
    Update sensor properties
    :return: uuid and status code
    """
    data = request.json
    print data
    if "resource_id" not in data.keys() \
            or "value" not in data.keys() \
            or not data.get("resource_id") \
            or not data.get("value") \
            or not isinstance(data.get("value"), dict):
        abort(400)
    _compose_sensor_tag(data)
    updated_res = resource.update_resource(id=data['resource_id'], **data["value"])
    return jsonify(resource_id=updated_res.get("id")), 200


@app.route('/get_geo_location')
@login_required
def get_geo_location():
    """Get the Geolocation of the current account"""
    location = gateway.get_gateway(gateway_id=session.get('gateway_id'))
    # remove unnecessary keys
    location.pop('url', None)
    return jsonify({'geo': location}), 201


@app.route('/update_sensor', methods=['PUT'])
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
    print "content: " + str(content)
    sensor = Sensor(uuid=res.get('uuid'), path=res.get('path'), gateway_id=session.get('gateway_id'))
    try:
        sts = sensor.update_status(data)
        return jsonify({'status': sts}), 201
    except IoTRequestError:
        abort(500)


@app.route('/add_sensor_group', methods=['POST'])
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


@app.route('/')
def root():
    return redirect(url_for('login'), code=302)


@app.route('/login')
def login():
    return render_template('login.html', 
                           static_url_prefix=static_url_prefix)


@app.route('/index')
@login_required
def index():
    return render_template('home_dashboard.html',
                           static_url_prefix=static_url_prefix)


@app.route('/energy')
def energy():
    return render_template('energy_dashboard.html',
                           static_url_prefix=static_url_prefix)


@app.route('/cf_instance')
@login_required
def get_instance():
    """
    Get instance ID and total running instances in the CF Cloud
    Return data in json format
    Not implemented yet for k8s
    """
    inst = {}
    return jsonify({'cf_instance': inst}), 201


@app.route('/get_groups')
@login_required
def list_sensor_groups():
    """
    Get the sensor groups of the current gateway
    Return data in json format
    """
    gateway_id = session['gateway_id']
    sg = sensor_group.get_all_groups(gateway_id=gateway_id)
    return jsonify(sensor_groups=sg)


@app.route('/get_gateways')
def list_gateways():
    # todo: need some security mechanism to protect the data
    # list all registered gateways
    gateways = gateway.list_gateways()

    keyword = config.get_map_keyword()
    types = config.get_map_types()
    return jsonify({'gateways': gateways,
                    'keyword': keyword,
                    'types': types}), 201


@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']
    password_sha = hashlib.sha256(password).hexdigest()
    if password_sha == user.login(username):
        gateway_id = user.user_gatewayid(username)
        # url = user.user_url(username)
        session['gateway_id'] = str(gateway_id)
        session['username'] = username
        info = 'Welcome ' + username
        print info
        resp = make_response(redirect(url_for('index'), code=302))
        resp.set_cookie('JSESSIONID', 'Sticky session.')
        resp.set_cookie('gateway_id', str(gateway_id))
        return resp
    else:
        info = 'Username or password are incorrect'
        return render_template('login.html', info=info,
                               static_url_prefix=static_url_prefix)


@app.route('/logout')
def logout():
    session.pop('gateway_id', None)
    session.pop('username', None)
    resp = make_response(redirect(url_for('login'), code=302))
    resp.set_cookie('__VCAP_ID__', '', expires=0)
    return resp


@socketio.on('my temp', namespace='/index')
def get_temp(message):
    today_date_str = message.get('today_date')
    data, error = None, None
    print today_date_str

    try:
        today_date = datetime.datetime.strptime(today_date_str, "%m/%d/%Y").date()
    except ValueError:
        error = "Invalid date format: " + today_date_str

    start_date = today_date - timedelta(days=3)
    end_date = today_date + timedelta(days=3)
    print start_date, end_date

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
    print "######temp_actual#######"
    max_date = his_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(end))
    if not max_date:
        return []
    his_weather_info = his_weather.get_weather_by_date(start, end, region_id=session.get('gateway_id'),
                                                       created_at={'ge': str(max_date[0][0])},
                                                       order_by=[('publish_date', False)])
    print his_weather_info

    # convert the date object to string
    for info in his_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
    return his_weather_info


def temp_future(start, end):
    print "######temp_future#######"
    max_date = actual_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(start))
    if not max_date:
        return []
    actual_weather_info = actual_weather.get_weather_by_date(start, end, region_id=session.get('gateway_id'),
                                                             created_at={'ge': str(max_date[0][0])},
                                                             order_by=[('publish_date', False)])
    print actual_weather_info
    for info in actual_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
        info['forecast_date'] = info['forecast_date'].strftime('%Y-%m-%d')
    return actual_weather_info


def temp_today(start, end):
    print "######temp_today#####"
    max_date = actual_weather.get_max_date(gateway_id=session.get('gateway_id'), publish_date=str(start))
    if not max_date:
        return []
    actual_weather_info = actual_weather.get_weather_by_date(start, end, order=0, region_id=session.get('gateway_id'),
                                                             created_at={'ge': str(max_date[0][0])},
                                                             order_by=[('publish_date', False)])
    print actual_weather_info
    for info in actual_weather_info:
        info['publish_date'] = info['publish_date'].strftime('%Y-%m-%d')
        info['forecast_date'] = info['forecast_date'].strftime('%Y-%m-%d')
    return actual_weather_info


@socketio.on('my power', namespace='/index')
def get_power(message):
    today_date_str = message.get('today_date')
    data, error = None, None
    print today_date_str

    try:
        today_date = datetime.datetime.strptime(today_date_str, "%m/%d/%Y").date()
    except ValueError:
        error = "Invalid date format: " + today_date_str

    start_date = today_date - timedelta(days=3)
    end_date = today_date + timedelta(days=3)
    print start_date, end_date

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
    print "######power_actual#######"
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
    print "#########power_predict#########"
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
    admin_host = os.getenv("ADMIN_SERVICE_HOST", "")
    admin_port = os.getenv("ADMIN_SERVICE_NODE_PORT", "")
    if data_model:
        if env_str:
            # Running in Cloud Foundry env
            env_dict = json.loads(env_str)
            uris = env_dict.get("application_uris", None)
            if uris:
                admin_uri = uris[0].split(".")
                admin_uri[0] = "smarthome-adminportal"
                admin_uri = ".".join(admin_uri)
        elif admin_host:
            # Running in Kubernetes pod container
            admin_uri = "http://{}:{}/images/model/".format(admin_host, admin_port)
        elif os.path.isfile('/.dockerenv'):
            # Running in pure docker container
            admin_uri = "image/model/"
        else:
            # Running in physical machine
            admin_uri = "http://localhost:4000/images/model/"
    emit('my model resp', admin_uri + data_model['data_model']['name'] + ".png" if data_model and admin_uri else data_model)


if __name__ == '__main__':
    logger = logsettings.setup_log()
    logger.info('init SMART HOME project ...')
    port = os.getenv('PORT', '3000')
    socketio.run(app, debug=True, port=int(port), host="0.0.0.0")

