from functools import wraps
from flask import abort, flash, redirect, url_for
from flask.ext.login import current_user
from .models import Permission

def confirmation_required():
    """
    Later, just send it back one page. Or find some other way...
    http://flask.pocoo.org/snippets/120/
    http://flask.pocoo.org/snippets/62/
    :return:
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.confirmed:
                flash("You must confirm your email before you do that.")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)  # 403 is forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)