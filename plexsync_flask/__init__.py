import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from celery import Celery
import logging
import sys
from config import config, Config

# Flask extensions
db = SQLAlchemy()
bootstrap = Bootstrap()
socketio = SocketIO()
celery = Celery(__name__,
                worker_redirect_stdouts_level=logging.DEBUG,
                task_track_started=Config.CELERY_CONFIG['CELERY_TASK_TRACK_STARTED'],
                broker=Config.CELERY_CONFIG['CELERY_BROKER_URL'],
                backend=Config.CELERY_CONFIG['CELERY_RESULT_BACKEND'])
celery.config_from_object('celeryconfig')

# Import models so that they are registered with SQLAlchemy
from . import models  # noqa

# Import celery task so that it is registered with the Celery workers
from .tasks import *

# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events  # noqa

def create_app(config_name=None, main=True):
    if config_name is None:
        config_name = os.environ.get('PLEXSYNC_FLASK_CONFIG', 'development')
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    FORMAT = "[%(level)s in %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    formatter = logging.Formatter(FORMAT)
    app.logger.formatter = formatter
    app.config.from_object(config[config_name])
    logging.getLogger('socketio').setLevel(logging.ERROR)
    logging.getLogger('engineio').setLevel(logging.ERROR)
    app.maybecelery = celery


    # Initialize flask extensions
    db.init_app(app)
    bootstrap.init_app(app)
    if main:
        # Initialize socketio server and attach it to the message queue, so
        # that everything works even when there are multiple servers or
        # additional processes such as Celery workers wanting to access
        # Socket.IO
        socketio.init_app(app,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
                          debug=app.config['SOCKETIO_DEBUG']  )
    else:
        # Initialize socketio to emit events through through the message queue
        # Note that since Celery does not use eventlet, we have to be explicit
        # in setting the async mode to not use it.
        socketio.init_app(None,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
                          debug=app.config['SOCKETIO_DEBUG'],
                          async_mode='threading')
    celery.conf.update(config[config_name].CELERY_CONFIG)

    # Register web application routes
    from .plexsync_flask import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Register async tasks support
    from .tasks import tasks_bp as tasks_blueprint
    app.register_blueprint(tasks_blueprint, url_prefix='/task')

    return app
