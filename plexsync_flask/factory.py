from datetime import timedelta
from flask import Flask
from flask_socketio import SocketIO
from celery import Celery
from config import config

import logging
import os

socketio = SocketIO()
celery = Celery()

def get_logger(app):
    return logging.getLogger(app.import_name)

def make_celery(app, main=True):
    socketio = make_socketio(main=main, app=app)


    class ContextTask():
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            kwargs={}
            kwargs['exc_info']=exc
            log.error(f'Task {task_id} failed to execute', **kwargs)
            super().on_failure(exc, task_id, args, kwargs, einfo)

        def after_return(self, status, retval, task_id, args, kwargs, einfo):
            log.warn(f"after return self: {self}")
            log.warn(f"after return status {status}")
            log.warn(f"after return retval {retval}")
            log.warn(f"after return task_id {task_id}")
            log.warn(f"after return args {args}")
            log.warn(f"after return kwargs {kwargs}")

            log.warn(f"after return einfo {einfo}")
            data = {'result': retval}

            with app.app_context():
                 socketio.emit('comparison_done', {'html': retval}, namespace='/plexsync')
    if main:
        print("no, I'm in main")
        celery = Celery(
            app.import_name,
            backend=app.config['CELERY_RESULT_BACKEND'],
            broker=app.config['CELERY_BROKER_URL'])
            #include='plexsync.tasks')


        celery.Task = ContextTask()
        celery.conf.update(app.config)

        
    else:
        print("am I the baddy?")
        celery = Celery(
            app.import_name,
            backend=app.config['CELERY_RESULT_BACKEND'],
            broker=app.config['CELERY_BROKER_URL'])
#            include='plexsync.tasks')
    return celery

def make_socketio(app, main=True):
    socketio = SocketIO()

    # Initialize flask extensions
    if main:
        # Initialize socketio server and attach it to the message queue, so
        # that everything works even when there are multiple servers or
        # additional processes such as Celery workers wanting to access
        # Socket.IO
        socketio.init_app(app, debug=app.config['DEBUG'],
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    else:
        # Initialize socketio to emit events through through the message queue
        # Note that since Celery does not use eventlet, we have to be explicit
        # in setting the async mode to not use it.
        socketio.init_app(None, debug=app.config['DEBUG'],
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
                          async_mode='threading')

    return socketio

