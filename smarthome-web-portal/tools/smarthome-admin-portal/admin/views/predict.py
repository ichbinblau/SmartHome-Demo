# -*- coding: utf-8 -*-
import json
import logging
from jinja2 import TemplateNotFound
from flask import session, render_template, request, Blueprint, abort
from . import login_required
from admin.machine_learning import predict

predict_bp = Blueprint('predict', __name__)
logger = logging.getLogger(__name__)


@predict_bp.route('/href_predict/', methods=['GET'])
@login_required
def href_predict():
    try:
        return render_template('predict.html', username=session.get('username'))
    except TemplateNotFound:
        abort(404)


@predict_bp.route('/predict', methods=['PUT'])
@login_required
def prediction():
    content = request.get_json(silent=True)
    model_name = content.get('model_name')
    input_value = content.get('input_value')
    if not model_name or not isinstance(input_value, (int, long, float)):
        abort(400)
    r_value = predict.predict(model_name, 2, input_value)
    json_str = json.dumps(r_value)
    logger.debug(json_str)
    return json_str, 200
