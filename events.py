from . import create_app
from .factory import make_socketio, make_celery, get_logger
from plexsync.plexsync import PlexSync

app = create_app(main=False)
socketio = make_socketio(app=app, main=False)
logger = get_logger(app)

@socketio.on('comparison_done', namespace='/plexsync')
def plexsync_message(message):
   logger.debug(f"comparison re emitted {message}")


@socketio.on('render_template', namespace='/plexsync')
def render_template(message):
    logger.info(f"rendering template for {message.get('guid')}")
    logger.debug(f"message: {message}")

    plexsync = PlexSync()
    plexsync.render(message)
    
@socketio.on('broadcast', namespace='/plexsync')
def plexsync_broadcast(message):
    socketio.emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/plexsync')
def plexsync_connect():
    logger.info('Client connected')
    socketio.emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/plexsync')
def plexsync_disconnect():
    logger.info('Client disconnected')
