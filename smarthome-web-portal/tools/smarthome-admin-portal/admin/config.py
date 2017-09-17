# -*- coding: utf-8 -*-
"""
app settings
"""
import os
import hashlib
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

KEY_SIZE = 32
SECRET_KEY = os.urandom(KEY_SIZE)

DEBUG = True

SQLALCHEMY_TRACK_MODIFICATIONS = True
PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

#from admin.utils import get_vcap_service
#SQLALCHEMY_DATABASE_URI = get_vcap_service()

ADMIN_PWD = hashlib.sha256('admin').hexdigest()
UPLOAD_FOLDER = os.path.join(basedir, 'dataset')
Model_Seria_FOLDER = os.path.join(basedir, 'model', 'seria')
Model_Pic_FOLDER = os.path.join(basedir, 'static', 'images', 'model')

FORECAST_URL = "https://query.yahooapis.com/v1/public/yql"
HISTORICAL_URL = "http://api.wunderground.com/api/563fd474dd62bc34/"
FORECAST_RANGE = 3
PROXY = {
    'http': os.environ.get('proxy', None),
    'https': os.environ.get('proxy', None)
}

