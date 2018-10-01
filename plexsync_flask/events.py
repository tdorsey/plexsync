from flask import g, session

from . import db, socketio, celery
from .models import User, Message
from .auth import verify_token


def push_model(model):
    """Push the model to all connected Socket.IO clients."""
    socketio.emit('updated_model', {'class': model.__class__.__name__,
                                    'model': model.to_dict()})


@socketio.on('ping_user')
def on_ping_user(token):
    """Clients must send this event periodically to keep the user online."""
    verify_token(token, add_to_session=True)
    if g.current_user:
        # Mark the user as still online
        g.current_user.ping()


@celery.task
def post_message(user_id, data):
    """Celery task that posts a message."""
    from .wsgi_aux import app
    with app.app_context():
        user = User.query.get(user_id)
        if user is None:
            return

        # Write the message to the database
        msg = Message.create(data, user=user, expand_links=False)
        db.session.add(msg)
        db.session.commit()

        # broadcast the message to all clients
        push_model(msg)

        if msg.expand_links():
            db.session.commit()

            # broadcast the message again, now with links expanded
            push_model(msg)

        # clean up the database session
        db.session.remove()


@socketio.on('post_message')
def on_post_message(data, token):
    """Clients send this event to when the user posts a message."""
    verify_token(token, add_to_session=True)
    if g.current_user:
        post_message.apply_async(args=(g.current_user.id, data))


@socketio.on('disconnect')
def on_disconnect():
    """A Socket.IO client has disconnected. If we know who the user is, then
    update our state accordingly.
    """
    nickname = session.get('nickname')
    if nickname:
        # we have the nickname in the session, we can mark the user as offline
        user = User.query.filter_by(nickname=nickname).first()
        if user:
            user.online = False
            db.session.commit()
            push_model(user)

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
