# -*- coding: utf-8 -*-
import os
import json
import time
import logging
from jinja2 import TemplateNotFound
from flask import session, render_template, request, Blueprint, flash, redirect, url_for, abort
from . import login_required
from werkzeug.utils import secure_filename
from admin.models import db, DataSet, _wrapper_dict
from admin.config import UPLOAD_FOLDER, Model_Seria_FOLDER, Model_Pic_FOLDER

dataset_bp = Blueprint('dataset', __name__)
logger = logging.getLogger(__name__)


@dataset_bp.route('/href_dataset/', methods=['GET'])
@login_required
def href_dataset():
    try:
        return render_template('dataset.html', username=session.get('username'))
    except TemplateNotFound:
        abort(404)


@dataset_bp.route('/dataset', methods=['GET'])
@login_required
def list_all_dataset():
    obj = db.session.query(DataSet).filter(DataSet.status == "1").all()
    info = _wrapper_dict(obj, ['id', 'filename', 'dataformat', 'title', 'rows', 'columns', 'rows', 'description',
                               'uploadtime', 'status'])
    json_str = json.dumps(info)
    logger.debug(json_str)
    return json_str, 200


@dataset_bp.route('/dataset/create', methods=['POST'])
@login_required
def create_dataset():
    # upload the file
    file = request.files['file']

    logger.debug(file.filename)
    filename = secure_filename(file.filename)
    logger.debug(filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    title = request.form['title']
    dataformat = "CSV"
    rows = 356
    columns = 3
    description = "This is dataset for shanghai 2013 year"
    uploadtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    status = "1"
    logger.debug(uploadtime)
    ds = DataSet(filename, dataformat, title, rows, columns, description, uploadtime, status)
    db.session.add(ds)
    db.session.commit()
    flash('The Dataset was successfully created.')
    return redirect(url_for('dataset.href_dataset'), code=302)


@dataset_bp.route('/dataset/delete', methods=['POST'])
@login_required
def delete_dataset():
    content = request.get_json(silent=True)
    title = content.get('title')
    obj = db.session.query(DataSet).filter(DataSet.title == title).all()
    logger.debug("---delete---")
    logger.debug(title)
    db.session.query(DataSet).filter(DataSet.title == title).delete()
    db.session.commit()

    filename = obj[0].filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    logger.debug(filepath)
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.debug("delete successful")
    return redirect(url_for('dataset.list_all_dataset'), 302)
