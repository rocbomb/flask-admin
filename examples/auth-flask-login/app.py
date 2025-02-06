import os

import flask_admin as admin
import flask_login as login
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_admin import expose
from flask_admin import helpers
from flask_admin.contrib import sqla
from flask_admin.theme import Bootstrap4Theme
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from wtforms import fields
from wtforms import form
from wtforms import validators

from couse import CourseList
from student import students_data
import logging
from logging.handlers import TimedRotatingFileHandler


# 配置日志
log_path = './logs/logfile.log'  # 日志文件的路径
if not os.path.exists(os.path.dirname(log_path)):
    os.makedirs(os.path.dirname(log_path))


# 设置日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# 设置日志轮转
handler = TimedRotatingFileHandler(log_path, when='midnight', interval=1, backupCount=30)
handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger('my_logger')
logger.addHandler(handler)


# Create Flask application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config["SECRET_KEY"] = "123456790"

# Create in-memory database
app.config["DATABASE_FILE"] = "test2.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)



# Create user model.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    login = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(80))
    password = db.Column(db.String(64))
    courses_list = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean)

    # Flask-Login integration
    # NOTE: is_authenticated, is_active, and is_anonymous
    # are methods in Flask-Login < 0.3.0
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.name

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    desc = db.Column(db.String(256))

class CourseVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    desc = db.Column(db.String(256))
    time = db.Column(db.Integer)

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError("用户不存在")
    
        if not user.is_admin:
            raise validators.ValidationError("该用户不是管理员")

        # we're comparing the plaintext pw with the the hash from the db
        if not user.password == self.password.data:
            # to compare plain text passwords use
            # if user.password != self.password.data:
            raise validators.ValidationError("密码错误")

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.StringField(validators=[validators.InputRequired()])
    email = fields.StringField()
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(login=self.login.data).count() > 0:
            raise validators.ValidationError("Duplicate username")


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)


# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated


# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):
    @expose("/")
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        link = (
            "<p>Don't have an account? <a href=\""
            + url_for(".register_view")
            + '">Click here to register.</a></p>'
        )
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super().index()

    @expose("/register/", methods=("GET", "POST"))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = form.password.data

            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for(".index"))
        link = (
            '<p>Already have an account? <a href="'
            + url_for(".login_view")
            + '">Click here to log in.</a></p>'
        )
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super().index()

    @expose("/logout/")
    def logout_view(self):
        login.logout_user()
        return redirect(url_for(".index"))


# Flask views
@app.route("/")
def index():
    return render_template("index.html")


# Initialize flask-login
init_login()

# Create admin
admin = admin.Admin(
    app,
    "Example: Auth",
    index_view=MyAdminIndexView(),
    theme=Bootstrap4Theme(base_template="my_master.html"),
)

# Add view
admin.add_view(MyModelView(User, db.session))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    import random
    import string

    db.drop_all()
    db.create_all()
    # passwords are hashed, to use plaintext passwords instead:
    # test_user = User(login="test", password="test")
    test_user = User(login="test", phone="test", name = "test", password="test")
    db.session.add(test_user)

    for student in students_data:
        user = User()
        user.name = student["name"]

        user.login = student["phone"]
        user.phone = student["phone"]

        user.is_admin = str(user.login) in ["17855860372"]

        user.password = str(student["password"])
        user.courses_list = student["courses"]
        db.session.add(user)

    db.session.commit()
    return






if __name__ == "__main__":
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config["DATABASE_FILE"])
    if not os.path.exists(database_path):
        with app.app_context():
            build_sample_db()

    # Start app
    app.run(debug=True)
