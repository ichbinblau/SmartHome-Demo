# -*- coding: utf-8 -*-
"""
util functions
"""
import datetime
import json
import os


def get_utc_now():
    return datetime.datetime.utcnow()


def format_datetime(date_time):
    """Generate string from datetime object."""
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def get_mysql_conn_str():
    mysql_host = os.getenv('MYSQL_MASTER_SERVICE_HOST', None)
    if mysql_host:
        return "mysql+pymysql://root:intel123@{}:3306/smart_home?charset=utf8".format(mysql_host)
    else:
        return 'mysql+pymysql://root:zaq12wsx@localhost:13306/smart_home'

