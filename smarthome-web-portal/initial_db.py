#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to pre-populate the database
"""
import hashlib
from sqlalchemy_utils.functions import create_database, database_exists
from DB.api import user, gateway, sensor_type, sensor_group
from DB.api import database
from DB import exception
from utils.config import config

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass


def hash_str(raw_str):
    return hashlib.sha256(raw_str).hexdigest()

DEFAULT_GATEWAYS = [
    {
        'name': 'lab',
        'url': 'http://172.17.0.2:8000/',
        'address': 'No. 880, Zi Xing Rd, Shanghai',
        'latitude': '31.020780',
        'longitude': '121.454648',
        'status': True
    },
    {
        'name': 'demo',
        'url': 'http://192.55.66.110:8000/',
        'address': 'Manchester Grand Hyatt San Diego',
        'latitude': '32.714987',
        'longitude': '-117.167359',
        'status': True
    },
]

DEFAULT_USERS = [
    {
        'username': 'dev',
        'password': hash_str('P@ssw0rd'),
    },
    {
        'username': 'OTC',
        'password': hash_str('!otivity'),
    },
]

SENSOR_TYPES = [
    ('fan', 'oic.r.fan'),
    ('motion', 'oic.r.sensor.motion'),
    ('gas', 'oic.r.sensor.carbondioxide'),
    ('solar', 'oic.r.solar'),
    ('illuminance', 'oic.r.sensor.illuminance'),
    ('buzzer', 'oic.r.buzzer'),
    ('temperature', 'oic.r.temperature'),
    ('rgbled', 'oic.r.colour.rgb'),
    ('led', 'oic.r.switch.binary'),
    ('button', 'oic.r.button'),
    ('power', 'oic.r.energy.consumption'),
    ('environment', 'oic.r.sensor.environment'),
    ('mp3player', 'x.com.intel.demo.mp3player'),
    ('audio', 'oic.r.audio'),
    ('brightness', 'oic.r.light.brightness'),
    ('generic', 'generic'),
]

SENSOR_GROUPS = [
    ('Kitchen', '#cd8daa'),
    ('Bedroom', '#f19d5a'),
    ('Living Room', '#7499e1'),
]


def new_database():
    engine = config.get_connection_url()
    if not database_exists(engine):
        print "Create database " + engine
        create_database(engine)
        return True
    elif not database.check_tables():
        print "Check tables and incomplete tables."
        return True
    return False


def create_tables():
    print "Truncate the database if it exists..."
    database.drop_db()
    print "Create the database tables ..."
    database.create_db()


def init_data():
    print "Init gateway data ..."
    gw_ids = list()
    for gw in DEFAULT_GATEWAYS:
        new_gateway = gateway.add_gateway(gw)
        gw_ids.append(new_gateway.get('id'))
    print "Init user data ..."
    for index, usr in enumerate(DEFAULT_USERS):
        usr.update({'gateway_id':
                    gw_ids[index]})
        user.add_user(usr)
    print "Init sensor type data ..."
    for st in SENSOR_TYPES:
        sensor_type.new({'type': st[1], 'mapping_class': st[0]})
    print "Init sensor groups ..."
    for sg in SENSOR_GROUPS:
        for i in range(len(DEFAULT_GATEWAYS)):
            sensor_group.new({'gateway_id': gw_ids[i], 'name': sg[0], 'color': sg[1]})
    print "Done."


if __name__ == "__main__":
    try:
        if new_database():
            create_tables()
            init_data()
    except exception.DatabaseException as e:
        print e.message

