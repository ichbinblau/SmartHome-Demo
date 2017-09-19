# -*- coding: utf-8 -*-
from flask import session, render_template, request, Blueprint, flash, redirect, url_for, jsonify
from . import login_required
from admin.models import db, Gateway, _wrapper_dict
from sqlalchemy.exc import IntegrityError

gw_bp = Blueprint('gateway', __name__, )


FORM_DATA = ['name', 'url', 'address', 'latitude', 'longitude']
@gw_bp.route('/gateway/update/<int:gw_id>', methods=['PUT', 'POST'])
@login_required
def update_gw(gw_id):
    if request.method == 'POST':
        post = {}
        for key in FORM_DATA:
            post[key] = request.form.get(key, None)
        gw = Gateway.get_or_404(gw_id)
        gw.update(**post)
        db.session.commit()
        flash('The entry was successfully updated.')
    return redirect(url_for('gateway.list_all_gws'), 302)


@gw_bp.route('/gateway/create', methods=['POST'])
@login_required
def create_gw():
    post = {}
    for key in FORM_DATA:
        post[key] = request.form.get(key, None)
    gw = Gateway.create(**post)
    print gw
    db.session.commit()
    flash('The entry was successfully created.')
    return redirect(url_for('gateway.list_all_gws'), 302)


@gw_bp.route('/gateways/', methods=['GET'])
@login_required
def list_all_gws():
    obj = Gateway.query.order_by(Gateway.id).all()
    info = _wrapper_dict(obj, ['id', 'name', 'url', 'address', 'latitude', 'longitude', 'created_at'])
    print info
    return render_template('list.html', gateways=info, username=session.get('username'))


@gw_bp.route('/gateway')
@gw_bp.route('/gateway/<int:gw_id>', methods=['GET'])
@login_required
def show_gw(gw_id=None):
    info = None
    if gw_id:
        gw = Gateway.get_or_404(gw_id)
        info = _wrapper_dict(gw, ['id', 'name', 'url', 'address', 'latitude', 'longitude'])
    return render_template('edit.html', gateway=info, username=session.get('username'))


@gw_bp.route('/gateway/delete', methods=['POST', 'DELETE'])
@login_required
def delete_gw():
    if request.method == 'POST':
        gw_str = request.form.get('id', None)
        print gw_str
        if gw_str:
            gw_list = gw_str.split(',')
            for gw_id in gw_list:
                try:
                    gw = Gateway.get_or_404(gw_id)
                    gw.delete()
                    flash('Gateway {} was successfully deleted.'.format(str(gw_str)))
                except IntegrityError:
                    flash('Unable to delete gateway {} because it has remaining user bindings. Plz check.'.format(str(gw_str)))
    return redirect(url_for('gateway.list_all_gws'), 302)


@gw_bp.route('/gateway/<gateway_name>')
def check_gw_exists(gateway_name=None):
    if gateway_name:
        exists = db.session.query(db.session.query(Gateway).filter_by(name=gateway_name).exists()).scalar()
        if not exists:
            return jsonify(result=True), 200
    return jsonify(result=False), 200
