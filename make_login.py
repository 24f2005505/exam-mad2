from model import User
from werkzeug.security import check_password_hash
from flask import request, jsonify
from flask_login import login_required, login_user, logout_user, current_user


def user_data(user):
    ## what the vue app gets to know about the logged in user
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "fname": user.fname,
        "lname": user.lname
    }
    return data


def make_login(app):
    @app.route('/api/me')
    def me():
        ## vue asks this on page load to know who is logged in
        if not current_user.is_authenticated:
            return jsonify(user=None)
        return jsonify(user=user_data(current_user))


    @app.route('/api/login', methods = ["POST"])
    def login():
        data = request.get_json()
        username = data.get("username")
        pwd_hash = data.get("password")
        user = User.query.filter_by(username = username).first()
        if user and check_password_hash(user.pwd_hash, pwd_hash) and not user.admin_enforced_blacklist_status:
            role = user.role
            if role not in ("admin", "student", "examiner"):
                return jsonify(error="Invalid user role. Please contact support."), 403
            if role == "examiner" and user.examiner.status != "active":
                return jsonify(error="Your examiner account is inactive. Contact admin."), 403
            login_user(user) ## log in the user
            return jsonify(message="Login successful!", user=user_data(user))
        elif user and user.admin_enforced_blacklist_status:
            return jsonify(error="Your account is banned, contact admin."), 403
        else:
            return jsonify(error="Invalid username or password. Please try again."), 401


    @app.route('/api/logout', methods = ["POST"])
    @login_required
    def logout():
        logout_user() ## log out the user
        return jsonify(message="Logged out successfully!")
