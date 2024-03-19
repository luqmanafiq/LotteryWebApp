# IMPORTS
import os
import logging
from flask_talisman import Talisman
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_qrcode import QRcode
from dotenv import load_dotenv


class SecurityFilter(logging.Filter):
    def filter(self, record):
        return 'SECURITY' in record.getMessage()


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'lottery.log'), 'a')
file_handler.setLevel(logging.WARNING)

# Add filter to file handler
file_handler.addFilter(SecurityFilter())
# create formatter
formatter = logging.Formatter('%(asctime)s : %(message)s', '%m/%d/%Y %I:%M:%S %p')
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)

load_dotenv()
# CONFIG
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_ECHO'] = os.getenv('SQLALCHEMY_ECHO') == 'True'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS') == 'True'

app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')

# initialise database
db = SQLAlchemy(app)

# custom content security policy
csp = {
    'default-src': [
        '\'self\'',
        'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'
    ],
    'frame-src': [
        '\'self\'',
        'https://www.google.com/recaptcha/',
        'https://recaptcha.google.com/recaptcha/'
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://www.google.com/recaptcha/',
        'https://www.gstatic.com/recaptcha/',
    ],
    'img-src': [
        'data:'
    ]
}

talisman = Talisman(app, content_security_policy=csp)
qrcode = QRcode(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'users.login'
login_manager.login_message = "Please log in to access this page."

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from models import User


# Authenticated users must be logged into the application (i.e. no longer anonymous)
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.errorhandler(400)
def bad_request_error(error):
    return render_template('errors.html', error_code=400, error_name="Bad Request Error"), 400


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors.html', error_code=403, error_name="Forbidden Error"), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors.html', error_code=404, error_name="Not Found Error"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('errors.html', error_code=500, error_name="Internal Error"), 500


@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('errors.html', error_code=503, error_name="Service Unavailable Error"), 503


# HOME PAGE VIEW
@app.route('/')
def index():
    return render_template('main/index.html')


# BLUEPRINTS
# import blueprints
from users.views import users_blueprint
from admin.views import admin_blueprint
from lottery.views import lottery_blueprint

#
# # register blueprints with app
app.register_blueprint(users_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(lottery_blueprint)

if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))
