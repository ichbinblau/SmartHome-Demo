# -*- coding: utf-8 -*-
"""
Celery settings
"""
from utils.config import config

# Change this to your settings
mq_conn_str = config.get_rabbitmq_conn_str()
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'rpc://'
BROKER_URL = mq_conn_str
CELERY_IMPORTS = ('CeleryTask.tasks',)
CELERY_REDIRECT_STDOUTS_LEVEL = 'INFO'
CELERY_CREATE_MISSING_QUEUES = True


