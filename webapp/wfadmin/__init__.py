from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from wfadmin.config import Config
from wfadmin.translations.default import strings
from os import path, system
import sys
sys.path.append('../')

# The stuff that the app needs
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"
login_manager.login_message = strings["LOGIN_MESSAGE"]
configuration = Config()


def service_running(service: str) -> bool:
    status = system(f"systemctl is-active --quiet {service}")
    return status == 0

def create_app(config_class=Config):
    # Initializing stuff
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # Making the language strings available globally to the templates
    app.jinja_env.globals.update(language_strings=strings)
    app.jinja_env.globals.update(service_running=service_running)
    from wfadmin.main.routes import main
    from wfadmin.errors.handlers import errors
    from wfadmin.api.routes import api
    app.register_blueprint(main)
    app.register_blueprint(api)
    app.register_blueprint(errors)
    print(f"Config('{Config.SECRET_KEY}', '{Config.RECAPTCHA_API_KEY}', '{Config.RECAPTCHA_SITE_KEY}', '{Config.SQLALCHEMY_DATABASE_URI}', '{Config.ENDPOINT_AUTOIP}')")

    return app
