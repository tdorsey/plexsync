import os
import logging
import uuid
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    FLASK_APP = 'plexsync-web'
    SECRET_KEY = os.environ.get('SECRET_KEY') or f"uuid.uuid1()"
    REQUESTS_CHUNKSIZE_BYTES = 1024 * 1024  #1MB
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    CELERY_CONFIG = {
                        'CELERY_BROKER_URL' : 'amqp://rabbitmq:rabbitmq@rabbitmq',
                        'CELERY_RESULT_BACKEND' : 'redis://redis:6379/0',
                        'CELERY_WORKER_REDIRECT_STDOUTS_LEVEL': logging.DEBUG,
                        'CELERY_TASK_TRACK_STARTED': True
                    }
    SOCKETIO_MESSAGE_QUEUE = 'redis://redis:6379/1'
    SOCKETIO_DEBUG = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_EMAIL = 'noreply@example.com'
    FLASKY_MAIL_SENDER = f'Flasky Admin <{FLASKY_EMAIL}>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
  
    @classmethod
    def init_app(cls, app):
            Config.init_app(app)
    #log to stdout
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            app.logger.addHandler(stream_handler)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SOCKETIO_DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
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
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
