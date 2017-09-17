# -*- coding: utf-8 -*-
from flask import session, render_template, request, Blueprint, flash, redirect, url_for, jsonify
from . import login_required
from admin.models import db, User, Gateway, _wrapper_dict


user_bp = Blueprint('user', __name__)


@user_bp.route('/users/', methods=['GET'])
@login_required
def list_all_users():
    obj = User.query.order_by(User.id).all()
    info = _wrapper_dict(obj, ['id', 'username', 'phone', 'gateway', 'created_at'])
    return render_template('list_users.html', users=info, username=session.get('username'))


@user_bp.route('/user/delete', methods=['POST', 'DELETE'])
@login_required
def delete_user():
    if request.method == 'POST':
        user_str = request.form.get('id', None)
        print user_str
        if user_str:
            user_list = user_str.split(',')
            print user_list
            for uid in user_list:
                u = User.get_or_404(int(uid))
                u.delete()
            flash('User {} was successfully deleted.'.format(str(user_str)))
    return redirect(url_for('user.list_all_users'), 302)


@user_bp.route('/user/<username>')
def check_user_exists(username=None):
    if username:
        exists = db.session.query(db.session.query(User).filter_by(username=username).exists()).scalar()
        if not exists:
            return jsonify(result=True), 200
    return jsonify(result=False), 200


USER_DATA = ['username', 'password', 'phone', 'gateway_id']
@user_bp.route('/user/create', methods=['POST'])
@login_required
def create_user():
    post = {}
    for key in USER_DATA:
        post[key] = request.form.get(key, None)
    user = User.create(**post)
    print user
    db.session.commit()
    flash('The entry was successfully created.')
    return redirect(url_for('user.list_all_users'), 302)


@user_bp.route('/user')
@user_bp.route('/user/<int:uid>', methods=['GET'])
@login_required
def show_user(uid=None):
    info = None
    if uid:
        user = User.get_or_404(uid)
        info = _wrapper_dict(user, ['id', 'username', 'phone', 'gateway_id', 'gateway'])
    obj = Gateway.query.all()
    gws = _wrapper_dict(obj, ['id', 'name', 'url', 'address', 'latitude', 'longitude', 'created_at'])
    return render_template('edit_user.html', user=info, gateways=gws, username=session.get('username'))


USER_FORM_DATA = ['phone', 'gateway_id', 'username']
@user_bp.route('/user/update/<int:uid>', methods=['PUT', 'POST'])
@login_required
def update_user(uid):
    if request.method == 'POST':
        post = {}
        for key in USER_FORM_DATA:
            post[key] = request.form.get(key, None)
        u = User.get_or_404(uid)
        u.update(**post)
        db.session.commit()
        flash('The entry was successfully updated.')
    return redirect(url_for('user.list_all_users'), 302)
