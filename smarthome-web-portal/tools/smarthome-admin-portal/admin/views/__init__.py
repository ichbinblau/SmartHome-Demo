# -*- coding: utf-8 -*-
import os
import functools
from flask import session, redirect, url_for


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('index.index', r=ord(os.urandom(1))))
    return wrapper
