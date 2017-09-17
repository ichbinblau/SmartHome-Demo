# -*- coding: utf-8 -*-
"""
util functions
"""
import datetime
import json
import os
from random import SystemRandom


def get_utc_now():
    return datetime.datetime.utcnow()


def format_datetime(date_time):
    """Generate string from datetime object."""
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def get_vcap_service():
    vcap_config = os.getenv('VCAP_SERVICES', None)
    if vcap_config:
        decoded_config = json.loads(vcap_config)
        for key, value in decoded_config.iteritems():
            if key.startswith('mysql56'):
                mysql_creds = decoded_config[key][0]['credentials']
                uri = str(mysql_creds['uri']).split("?")
                return "{}?charset=utf8".format(uri[0])
    else:
        return 'mysql+pymysql://root:zaq12wsx@localhost:13306/smart_home'


def gen_randint(start=0, stop=10):
    """
    Generate cryptographically secure random int
    :param start: start value
    :param stop: stop value
    :return: random int
    """
    cryptogen = SystemRandom()
    return cryptogen.randint(start, stop)

