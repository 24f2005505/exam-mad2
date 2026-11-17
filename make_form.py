from model import db, User, Student
from werkzeug.security import generate_password_hash as ph
from flask import request, jsonify
from utils import missing_fields

def username_unique(User, uname):
    bool_ = User.query.filter_by(username = uname).first() is None
    return bool_

def email_unique(User, email):
    bool_ = User.query.filter_by(email = email).first() is None
    return bool_

def make_form(app):

    @app.route('/api/register_student', methods = ["POST"])
    def register_student():
        ## handle unique username heere
        data = request.get_json()
        missing = missing_fields(data, ["fname", "lname", "username", "email", "password", "con_password", "gender", "university_name", "major", "gpa"])
        if missing:
            return jsonify(error=f"Please fill the {missing}."), 400
        if not username_unique(User, data["username"]):
            return jsonify(error="Username already taken, please choose another one."), 409
        elif not email_unique(User, data["email"]):
            return jsonify(error="This email is registered. Try logging in instead."), 409
        elif data["password"] != data["con_password"]:
            return jsonify(error="Passwords do not match, please re-enter."), 400
        else:
            user = User(
                    username= data["username"],
                    email= data["email"],
                    role = "student",
                    fname = data["fname"],
                    lname = data["lname"],
                    pwd_hash = ph(data["password"]),
                    gender = data["gender"],
                    admin_approval_status = "approved" ## students can log in right after registering
                )

            db.session.add(user)
            db.session.flush()

            student = Student(
                major = data["major"],
                sid = user.id,
                university = data["university_name"],
                gpa = data["gpa"]
            )

            db.session.add(student)
            db.session.commit()

        return jsonify(message="Registration successful!"), 201
