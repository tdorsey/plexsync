from flask import g, session, render_template, current_app, request
from flask_socketio import join_room, leave_room

from . import socketio, celery

import logging
log = logging.getLogger(__name__)

from plexsync import PlexSync
def dump(obj):
  for attr in dir(obj):
    log.warning("obj.%s = %r" % (attr, getattr(obj, attr)))

@socketio.on_error_default
def default_error_handler(e):
    log.warning(request.event["message"]) # "my error event"
    log.warning(request.event["args"])  


@socketio.on('comparison_done', namespace='/plexsync')
def plexsync_message(message):
    log.warning(f"Emitting comparison_done")
    socketio.emit(namespace='/plexsync')

@socketio.on('render_template', namespace='/plexsync')
def render_template(message):
    import jinja2
    from .wsgi_aux import app as aux
    with aux.app_context():
        plexsync = PlexSync()
        plexsync.getAccount()
        server = plexsync.getServer(message.get("server"))
        section = plexsync.getSection(server, message.get("section"))
        guid = message.get("guid")
        result = section.search(guid=guid).pop()
        template_data = plexsync.prepareMediaTemplate(result)
        try:
            log.debug(f"Template {template_data}")
            template = current_app.jinja_env.get_template("media.html")
            html = template.render(media=template_data)            
            socketio.emit('template_rendered', {'html': html}, namespace='/plexsync')
        except Exception as e:
            log.exception(e)
    return

@socketio.on('broadcast', namespace='/plexsync')
def plexsync_broadcast(message):
    socketio.emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/plexsync')
def plexsync_connect():
    log.warning(f"Client connected to room {request.sid}")

#@socketio.on('join', namespace='/plexsync')
#def plexsync_join(room):
#    join_room(room=room)
#    log.warning(f"Client {client} joined room {room}")

@socketio.on('disconnect', namespace='/plexsync')
def plexsync_disconnect():
    log.warning(f"Client disconnected from room {request.sid}")
