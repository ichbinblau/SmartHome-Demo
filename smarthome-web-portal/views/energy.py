# -*- coding: utf-8 -*-
import logging
from jinja2 import TemplateNotFound
from flask import Blueprint, render_template, abort


energy_blueprint = Blueprint('energy', __name__, )
logger = logging.getLogger(__name__)


@energy_blueprint.route('/energy')
def energy():
    try:
        return render_template('energy_dashboard.html', static_url_prefix="")
    except TemplateNotFound:
        abort(404)
