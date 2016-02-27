__author__ = 'Stuart'

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER = 'smtp.gmail.com'  # Not in China
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # for gmail
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # for gmail
    TIP_MAIL_SUBJECT_PREFIX = "[TOMT]"
    TIP_MAIL_SENDER = 'Tip of My Tongue Admin <admin@tomt.com>'
    TIP_MAIL_ADDRESS = 'admin@tomt.com'
    TIP_ADMIN = os.environ.get('TOMT_ADMIN')  # email addy that when recognized is auto-promoted to admin
    STRIPE_KEYS = {'secret_key': os.environ.get('STRIPE_SECRET_KEY'),
                   'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY')}
    SSL_DISABLE = True  # Don't need this except on Heroku
    SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
    SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
    TIP_AUTO_APPROVE = False
    CATEGORIES = ["music","people","movies","tv","things","language","nsfw","art"]  # when updated, update forms
    Q_PER_PAGE = 10
    # SQLALCHEMY_ECHO = True # to see what SQL statements being fired

    @staticmethod
    def init_app(app):
        """
        Takes app instance as arg.
        Here, config specific initialization can be performed.
        """
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    USE_RELOADER = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    TIP_AUTO_APPROVE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir,'data-test.sqlite')
    WTF_CSRF_ENABLED = False  # since extracting and parsing the CSRF token in tests is a bitch, easier to disable

class ProductionConfig(Config):
    import psycopg2
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir,'data.sqlite')

    @classmethod
    def init_app(cls, app):  # cls has to be 1st arg for class methods
        Config.init_app(app)

        # email errors to admins
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.TIP_MAIL_SENDER,
            toaddrs=[cls.TIP_ADMIN],
            subject=cls.TIP_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))  # Don't need to set to false on Heroku, non-existent == False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

config = {
    'development' : DevelopmentConfig,
    'testing' : TestingConfig,
    'production' : ProductionConfig,
    'heroku': HerokuConfig,
    #'unix': UnixConfig,

    'default': DevelopmentConfig,
}