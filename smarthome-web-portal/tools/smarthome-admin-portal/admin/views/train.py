# -*- coding: utf-8 -*-
import os
import json
import logging
from jinja2 import TemplateNotFound
from flask import session, render_template, request, Blueprint, flash, redirect, url_for, abort
from . import login_required
from admin.models import db, DataModel, DataSet, _wrapper_dict
from admin.config import UPLOAD_FOLDER, Model_Seria_FOLDER, Model_Pic_FOLDER
from admin.machine_learning import train

train_bp = Blueprint('train', __name__)
logger = logging.getLogger(__name__)


@train_bp.route('/href_training/', methods=['GET'])
@login_required
def href_training():
    try:
        return render_template('training.html', username=session.get('username'))
    except TemplateNotFound:
        abort(404)


@train_bp.route('/training', methods=['GET'])
@login_required
def list_all_models():
    obj = db.session.query(DataModel).filter(DataModel.status == "1").all()
    info = _wrapper_dict(obj, ['id', 'dataset_id', 'name', 'algorithm_type', 'serialization', 'description', 'created_at', 'status', 'dataset'])
    json_str2 = json.dumps(info)
    print json_str2
    return json_str2, 200


@train_bp.route('/training/create', methods=['POST'])
@login_required
def create_model():
    content = request.get_json(silent=True)
    model_name = content.get('model_name')

    dataset_title = content.get('dataset_title')
    obj_dataset = db.session.query(DataSet).filter(DataSet.title == dataset_title).all()
    dataset_id = obj_dataset[0].id
    dataset_filename = obj_dataset[0].filename
    dataset_path = os.path.join(UPLOAD_FOLDER, dataset_filename)
    pic_path = os.path.join(Model_Pic_FOLDER, model_name + ".png")
    train.train(dataset_path, os.path.join(Model_Seria_FOLDER, model_name), model_name, 2, pic_path)

    # write to DB
    algorithm_type = "Linear"
    serialization = 0
    description = "This is a model with Linear model"
    status = "1"

    dm = DataModel(dataset_id, model_name, algorithm_type, serialization, description, status)
    db.session.add(dm)
    db.session.commit()
    flash('The model was successfully created.')
    return redirect(url_for('train.list_all_models'), code=302)


@train_bp.route('/training/delete', methods=['PUT'])
@login_required
def delete_model():
    content = request.get_json(silent=True)
    model_name = content.get('model_name')
    obj = db.session.query(DataModel).filter(DataModel.name == model_name).all()
    print "---delete---"
    print model_name

    filename = "{}.pkl".format(model_name)
    print filename, Model_Seria_FOLDER
    filepath = os.path.join(Model_Seria_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        print "delete model file successful"
    else:
        print (filepath)

    pic_path = Model_Pic_FOLDER + model_name + ".png"
    if os.path.exists(pic_path):
        os.remove(pic_path)
        print "delete model pic successful"
    else:
        print pic_path

    db.session.query(DataModel).filter(DataModel.name == model_name).delete()
    db.session.commit()

    return redirect(url_for('train.list_all_models'), 303)
