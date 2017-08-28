# -*- coding: utf-8 -*-
"""
Celery tasks
"""
from __future__ import absolute_import
from CeleryTask.celeryapp import app
from CeleryTask.managers.data_manager import DataManager
from CeleryTask.managers.base import task_entry
from DB.api.gateway import list_gateways

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass


@app.task(name='CeleryTask.tasks.get_sensor_data', bind=True, ignore_result=True, default_retry_delay=30, max_retries=50)
def get_sensor_data(self, gw_id):
    try:
        mgr = DataManager(gw_id)
        task_entry(mgr)
    except Exception as exc:
        raise self.retry(exc=exc)


def call_tasks():
    app.control.purge()
    gw_list = list_gateways(status=True)
    for gw in gw_list:
        queue = 'iot_queue_{}'.format(str(gw.get('id')))
        get_sensor_data.apply_async((gw.get('id'),), queue=queue)
        # To tell all workers in the cluster to start consuming from the dynamically created queue
        app.control.add_consumer(queue, reply=True)


if __name__ == '__main__':
    call_tasks()











