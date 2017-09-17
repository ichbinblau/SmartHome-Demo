# -*- coding: utf-8 -*-
import hashlib
import logging
import os
from jinja2 import TemplateNotFound
from DB.api import user
from flask import request, session, make_response, redirect, url_for, Blueprint, render_template, abort

login_blueprint = Blueprint('login', __name__, )
logger = logging.getLogger(__name__)


@login_blueprint.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']
    password_sha = hashlib.sha256(password).hexdigest()
    if password_sha == user.login(username):
        gateway_id = user.user_gatewayid(username)
        # url = user.user_url(username)
        session['gateway_id'] = str(gateway_id)
        session['username'] = username
        info = 'Welcome ' + username
        logger.info(info)
        resp = make_response(redirect(url_for('now.index', r=ord(os.urandom(1))), code=302))
        resp.set_cookie('JSESSIONID', 'Sticky session.')
        resp.set_cookie('gateway_id', str(gateway_id))
        return resp
    else:
        info = 'Username or password are incorrect'
        return render_template('login.html', info=info,
                               static_url_prefix="")


@login_blueprint.route('/logout')
def logout():
    session.pop('gateway_id', None)
    session.pop('username', None)
    resp = make_response(redirect(url_for('.login'), code=302))
    resp.set_cookie('__VCAP_ID__', '', expires=0)
    return resp


@login_blueprint.route('/login')
def login():
    try:
        return render_template('login.html', static_url_prefix="")
    except TemplateNotFound:
        abort(404)


