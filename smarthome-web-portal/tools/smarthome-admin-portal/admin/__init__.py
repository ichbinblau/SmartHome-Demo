# -*- coding: utf-8 -*-
"""
Initialize Flask app
"""
from flask import Flask, session


def make_session_permanent():
    """Set session timeout: 5 mins (PERMANENT_SESSION_LIFETIME)"""
    session.permanent = True
    # app.permanent_session_lifetime = timedelta(minutes=5)


def create_app(debug=False):
    """Create an application."""
    """ static resource location"""
    # Create an Instance of Flask
    app = Flask(__name__, static_url_path='', )
    app.debug = debug

    # Include config from config.py
    app.config.from_object('admin.config')
    from admin.utils import get_vcap_service
    app.config['SQLALCHEMY_DATABASE_URI'] = get_vcap_service()
    app.before_request(make_session_permanent)

    from admin.models import db
    db.init_app(app)

    # from admin import models
    from views.login import login_bp
    from views.index import index_bp
    from views.user import user_bp
    from views.gateway import gw_bp
    from views.dataset import dataset_bp
    from views.predict import predict_bp
    from views.train import train_bp
    from views.gateway_model import gw_model_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(gw_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(train_bp)
    app.register_blueprint(gw_model_bp)

    return app

