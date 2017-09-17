# -*- coding: utf-8 -*-
import functools
import logging
from flask import abort, session
from flask.ext.socketio import emit, disconnect
from DB.api import resource
from utils import util
from . import socketio


logger = logging.getLogger(__name__)


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
    logger.debug(sensor, date_range, gateway_id)
    res_list = resource.list_resource(gateway_id=gateway_id)
    res_id = [res['id'] for res in res_list if res['sensor_type']['mapping_class'] == sensor]

    data = []
    if res_id:
        start_time = date_range[0]
        end_time = date_range[1]
        data = _get_historical_data(sensor, start_time, end_time, res_id)

    logger.debug(res_id, data)
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
