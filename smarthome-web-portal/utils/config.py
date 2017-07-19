# -*- coding: utf-8 -*-
"""
A module to parse configuration file in ini format
"""
import threading
import os
import json
import ConfigParser
from util import get_full_path
from utils.settings import CONFIG_FILE_NAME


class SingletonMixin(object):
    """ a singleton implementation"""
    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def instance(cls):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()
        return cls.__singleton_instance


class DefaultConfigParser(ConfigParser.RawConfigParser):
    """
    allow default value in settings.
    """
    def get_default(self, section, key, default=None):
        if self.has_option(section, key):
            return self.get(section, key)
        else:
            return default


class Configuration(SingletonMixin):
    """
    Singleton Config Parser Class
    """
    def __init__(self):
        self.mysql_host = None
        self.rabbitmq_host = None
        self._get_host_env()
        self.parser = DefaultConfigParser()
        self.parser.read(get_full_path('utils', CONFIG_FILE_NAME))

    def _get_host_env(self):
        self.mysql_host = os.getenv('MYSQL_MASTER_SERVICE_HOST', None)
        self.rabbitmq_host = os.getenv('RABBIT_SERVICE_SERVICE_HOST', None)

    @staticmethod
    def get_config_path():
        return get_full_path('utils', CONFIG_FILE_NAME)

    def get_log_path(self):
        log_name = self.parser.get_default('logging', 'log_name', 'SHProject.log')
        log_dir = self.parser.get_default('logging', 'log_dir', 'log')
        return get_full_path(log_dir, log_name)

    def _get_connection_url_from_file(self):
        host = self.mysql_host if self.mysql_host else self.parser.get_default('mysql', 'host', 'localhost')
        port = self.parser.get_default('mysql', 'port', '3306')
        username = self.parser.get_default('mysql', 'username', 'root')
        password = self.parser.get_default('mysql', 'password', 'zaq12wsx')
        database = self.parser.get_default('mysql', 'database', 'flask_test')
        return "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8".format(username, password, host, port, database)

    def _get_rabbitmq_conn_str_from_file(self):
        host = self.rabbitmq_host if self.rabbitmq_host else \
            self.parser.get_default('rabbitmq-server', 'host', 'localhost')
        port = self.parser.get_default('rabbitmq-server', 'port', '5672')
        username = self.parser.get_default('rabbitmq-server', 'username', 'guest')
        password = self.parser.get_default('rabbitmq-server', 'password', 'guest')
        return "amqp://{}:{}@{}:{}".format(username, password, host, port)

    def get_database_pool_type(self):
        return self.parser.get_default('mysql', 'database_pool_type', 'static')

    def get_all_proxy(self):
        return self.parser.get_default('proxy', 'all_proxy')

    def get_map_types(self):
        types = self.parser.get_default('map-filter', 'types', '')
        return types.split(',') if types else ''

    def get_map_keyword(self):
        return self.parser.get_default('map-filter', 'keyword', '')

    def get_api_key(self):
        return self.parser.get_default('SMS', 'api_key')

    def get_api_secret(self):
        return self.parser.get_default('SMS', 'api_secret')

    def get_sms_interval(self):
        return self.parser.get_default('SMS', 'interval', '600')

config = Configuration.instance()







