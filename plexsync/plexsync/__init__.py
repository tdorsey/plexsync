

# Import celery task so that it is registered with the Celery workers
from . import tasks

# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events

# Import factories to create the flask/socket/celery apps
from . import factory

