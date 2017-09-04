# -*- coding: utf-8 -*-
"""
Celery tasks
"""
from __future__ import absolute_import
import os
import datetime
from CeleryTask.celeryapp import app
from CeleryTask.managers.data_manager import DataManager
from CeleryTask.managers.activity_counter import ActivityCounter
from CeleryTask.managers.base import task_entry
from DB.api.gateway import list_gateways
from utils import util

DEMO_TIMEZONE = "America/Los_Angeles"


try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass


def generate_time_period(timezone=DEMO_TIMEZONE):
    """
    read timezone from env
    :param timezone:
    :return: the datetime period in utc format
    """
    tz = os.getenv('timezone')
    if not tz:
        tz = timezone
    tz_offset = util.get_utc_offset(tz)
    print tz_offset
    if not tz_offset:
        raise
    local_time = util.get_local_datetime_now(tz)
    return (util.format_datetime(util.toUTC(datetime.datetime(local_time.year, local_time.month,
                                                              local_time.day, 0, 0, 0, 0), tz)),
            util.format_datetime(util.toUTC(datetime.datetime(local_time.year, local_time.month,
                                                              local_time.day, 23, 59, 59), tz)))


@app.task(name='CeleryTask.tasks.count_activities', bind=True, ignore_result=True, default_retry_delay=5, max_retries=2)
def count_activities(self):
    time_period = generate_time_period()
    if not time_period:
        return
    try:
        mgr = ActivityCounter(time_period)
        task_entry(mgr)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(name='CeleryTask.tasks.get_sensor_data', bind=True, ignore_result=True, default_retry_delay=30, max_retries=50)
def get_sensor_data(self, gw_id):
    try:
        mgr = DataManager(gw_id)
        task_entry(mgr)
    except Exception as exc:
        raise self.retry(exc=exc)


def call_tasks():
    # app.control.purge()
    gw_list = list_gateways(status=True)
    for gw in gw_list:
        queue = 'iot_queue_{}'.format(str(gw.get('id')))
        get_sensor_data.apply_async((gw.get('id'),), queue=queue)
        # To tell all workers in the cluster to start consuming from the dynamically created queue
        app.control.add_consumer(queue, reply=True)


if __name__ == '__main__':
    call_tasks()










