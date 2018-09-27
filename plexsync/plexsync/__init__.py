from flask import Flask
from flask_socketio import SocketIO
from celery import Celery
from .app_config import Config as config

celery = Celery(__name__, broker=config.CELERY_BROKER_URL)
socketio = SocketIO()


# Import celery task so that it is registered with the Celery workers
from . import tasks

# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events

# Import factories to create the flask/socket/celery apps
from . import factory

