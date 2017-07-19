# -*- coding: utf-8 -*-
"""
Initialize Flask app
"""
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


# Create an Instance of Flask
app = Flask(__name__, static_url_path='')

# Include config from config.py
app.config.from_object('admin.config')
from admin.utils import get_mysql_conn_str
app.config['SQLALCHEMY_DATABASE_URI'] = get_mysql_conn_str()

# Create an instance of SQLAclhemy
db = SQLAlchemy(app)

from admin import views, models
