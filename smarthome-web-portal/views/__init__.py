# -*- coding: utf-8 -*-
from flask import Flask
from flask_socketio import SocketIO
from utils import logsettings
from utils.settings import SECRET_KEY

socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    """ static resource location"""
    static_url_prefix = ""
    app = Flask(__name__, static_url_path=static_url_prefix, static_folder='../static', template_folder='../templates')
    app.debug = debug
    app.config['SECRET_KEY'] = SECRET_KEY

    from .now import now_blueprint
    from .login import login_blueprint
    from .energy import energy_blueprint
    from . import before, future
    app.register_blueprint(login_blueprint)
    app.register_blueprint(now_blueprint)
    app.register_blueprint(energy_blueprint)

    socketio.init_app(app, pingTimeout=60)
    logger = logsettings.setup_log()
    return app
