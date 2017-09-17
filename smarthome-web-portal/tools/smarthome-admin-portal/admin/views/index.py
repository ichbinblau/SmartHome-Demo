# -*- coding: utf-8 -*-
from jinja2 import TemplateNotFound
from flask import session, render_template, abort, Blueprint

index_bp = Blueprint('index', __name__, )


@index_bp.route('/')
@index_bp.route('/index')
def index():
    try:
        return render_template('index.html', username=session.get('username'))
    except TemplateNotFound:
        abort(404)
