from functools import wraps
from flask import jsonify
from flask_login import current_user



def restrict(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify(error="Please login first."), 401

            if current_user.admin_enforced_blacklist_status:
                return jsonify(error="Your account is banned, contact admin."), 403

            if current_user.admin_approval_status == "not-approved":
                return jsonify(error="Your account is not approved, contact admin."), 403

            if current_user.admin_approval_status != "approved":
                return jsonify(error="Your account is not approved. Wait for admin approval."), 403

            if current_user.role != role:
                return jsonify(error="Access denied."), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

def all_restrict(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify(error="Please login first."), 401

            if current_user.role != role:
                return jsonify(error="Access denied."), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
