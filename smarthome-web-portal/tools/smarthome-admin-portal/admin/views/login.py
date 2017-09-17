# -*- coding: utf-8 -*-
import os
import hashlib
from flask import request, session, redirect, url_for, Blueprint, render_template, make_response
from admin.config import ADMIN_PWD


login_bp = Blueprint('login', __name__, )


@login_bp.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']
    password_sha = hashlib.sha256(password).hexdigest()
    if password_sha == ADMIN_PWD:
        session['username'] = username
        resp = make_response(redirect(url_for('index.index', r=ord(os.urandom(1))), code=302))
        resp.set_cookie('JSESSIONID', 'Admin sticky session.')
        return resp
    else:
        info = 'Username or password are incorrect'
        return render_template('index.html', info=info)


@login_bp.route('/logout')
def logout():
    session.pop('username', None)
    resp = make_response(redirect(url_for('index.index', r=ord(os.urandom(1))), code=302))
    resp.set_cookie('__VCAP_ID__', '', expires=0)
    return resp

