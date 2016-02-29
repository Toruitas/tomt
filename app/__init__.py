__author__ = 'Stuart'

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.pagedown import PageDown
import stripe
from config import config


bootstrap = Bootstrap()
db = SQLAlchemy()
mail = Mail()
pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection='basic'
login_manager.login_view='auth.login'



def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])  # gets configuration from config file's object by name
    config[config_name].init_app(app)  # runs init_app

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    pagedown.init_app(app)

    stripe.api_key = app.config['STRIPE_KEYS']['secret_key']  # remember to set. Does anything placed here?

    @app.context_processor
    def inject_list():
        """
        For header dropdown list. Is there any way to do this elsewhere?
        :return:
        """
        return {"categories_list":app.config["CATEGORIES"]}

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .payments import payments as payments_blueprint
    app.register_blueprint(payments_blueprint, url_prefix='/payments')

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)

    return app