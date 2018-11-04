from flask import g, session, render_template, current_app

from . import socketio, celery

import logging
log = logging.getLogger(__name__)

from plexsync import PlexSync
def dump(obj):
  for attr in dir(obj):
    log.warning("obj.%s = %r" % (attr, getattr(obj, attr)))

def push_model(model):
    """Push the model to all connected Socket.IO clients."""
    socketio.emit('updated_model', {'class': model.__class__.__name__,
                                    'model': model.to_dict()})


@socketio.on_error_default
def default_error_handler(e):
    log.warning(request.event["message"]) # "my error event"
    log.warning(request.event["args"])  

@celery.task
def post_message(user_id, data):
    from .wsgi_aux import app

    """Celery task that posts a message."""
    with app.app_context():
        user = User.query.get(user_id)
        if user is None:
            return

        # Write the message to the database
        msg = Message.create(data, user=user, expand_links=False)

        # broadcast the message to all clients
        push_model(msg)

        if msg.expand_links():

            # broadcast the message again, now with links expanded
            push_model(msg)



@socketio.on('post_message')
def on_post_message(data, token):
    """Clients send this event to when the user posts a message."""
    verify_token(token, add_to_session=True)
    if g.current_user:
        post_message.apply_async(args=(g.current_user.id, data))


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
    log.warning(f"Client connected")

@socketio.on('disconnect', namespace='/plexsync')
def plexsync_disconnect():
    socketio.emit('Client disconnected')
