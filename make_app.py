from flask import Flask
from model import db, User, Admin
from flask_login import LoginManager
from werkzeug.security import generate_password_hash as ph
import random
random.seed(200)
import string
import mimetypes
mimetypes.add_type("text/javascript", ".js") ## windows sometimes says .js is text/plain, browser needs javascript

def init_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///examination_portal.db" ## uri for the database

    db.init_app(app) ## connect the database with the Flask app
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role="admin").first() ## there is theoretically only one admin
        if admin_user is None:
            admin_user = User(
                id = 1,
                username= "admin123",
                email= "admin@gmail.com",
                role = "admin",
                fname = "Admin",
                lname = "123",
                pwd_hash = ph("admin123"),  ## default password for admin
                gender = "other",
                admin_approval_status = "approved",
                admin_enforced_blacklist_status = False
            )
            db.session.add(admin_user)
            db.session.commit()

            admin = Admin(
                id =1,
                aid = admin_user.id,
                status = True
            )
            db.session.add(admin)
            db.session.commit()

    ## now start the login manager
    logn_manager = LoginManager() ## manages user sessions and handles login/logout and also makes current_user available
    logn_manager.init_app(app)

    @logn_manager.user_loader
    def load_user_id(user_id):
        return db.session.get(User, int(user_id)) ## return the user object for the given user id


    return app
