# -*- coding: utf-8 -*-
"""
Module to store the global constants
"""
import os
from os.path import dirname


PROJECT_ROOT = dirname(dirname(__file__))

"""random secret key"""
KEY_SIZE = 32

SECRET_KEY = os.urandom(KEY_SIZE)

"""The config file name to load"""
CONFIG_FILE_NAME = 'SHProject.conf'


# Divide sensors into groups
ALERT_GRP = ['motion', 'gas', 'buzzer', 'button']
STATUS_GRP = ['led', 'fan', 'buzzer']
DATA_GRP = ['temperature', 'solar', 'illuminance', 'power', 'energy', 'environment']
BRILLO_GRP = ['rgbled', 'brightness', 'audio', 'mp3player']


