from functools import wraps
try:
    from io import BytesIO
except ImportError:  # pragma:  no cover
    from cStringIO import StringIO as BytesIO

from flask import Blueprint, abort, g, request
from werkzeug.exceptions import InternalServerError
from celery import states

from plexsync import PlexSync

from . import celery
from .utils import url_for

text_types = (str, bytes)
try:
    text_types += (unicode,)
except NameError:
    # no unicode on Python 3
    pass

tasks_bp = Blueprint('tasks', __name__)


@celery.task
def run_flask_request(environ):
    from .wsgi_aux import app

    if '_wsgi.input' in environ:
        environ['wsgi.input'] = BytesIO(environ['_wsgi.input'])

    # Create a request context similar to that of the original request
    # so that the task can have access to flask.g, flask.request, etc.
    with app.request_context(environ):
        # Record the fact that we are running in the Celery worker now
        g.in_celery = True

        # Run the route function and record the response
        try:
            rv = app.full_dispatch_request()
        except:
            # If we are in debug mode we want to see the exception
            # Else, return a 500 error
            if app.debug:
                raise
            rv = app.make_response(InternalServerError())
        return (rv.get_data(), rv.status_code, rv.headers)


def async(f):
    """
    This decorator transforms a sync route to asynchronous by running it
    in a background thread.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # If we are already running the request on the celery side, then we
        # just call the wrapped function to allow the request to execute.
        if getattr(g, 'in_celery', False):
            return f(*args, **kwargs)

        # If we are on the Flask side, we need to launch the Celery task,
        # passing the request environment, which will be used to reconstruct
        # the request object. The request body has to be handled as a special
        # case, since WSGI requires it to be provided as a file-like object.
        environ = {k: v for k, v in request.environ.items()
                   if isinstance(v, text_types)}
        if 'wsgi.input' in request.environ:
            environ['_wsgi.input'] = request.get_data()
        t = run_flask_request.apply_async(args=(environ,))

        # Return a 202 response, with a link that the client can use to
        # obtain task status that is based on the Celery task id.
        if t.state == states.PENDING or t.state == states.RECEIVED or \
                t.state == states.STARTED:
            return '', 202, {'Location': url_for('tasks.get_status', id=t.id)}

        # If the task already finished, return its return value as response.
        # This would be the case when CELERY_ALWAYS_EAGER is set to True.
        return t.info
    return wrapped


@tasks_bp.route('/status/<id>', methods=['GET'])
def get_status(id):
    """
    Return status about an asynchronous task. If this request returns a 202
    status code, it means that task hasn't finished yet. Else, the response
    from the task is returned.
    """
    task = run_flask_request.AsyncResult(id)
    if task.state == states.PENDING:
        abort(404)
    if task.state == states.RECEIVED or task.state == states.STARTED:
        return '', 202, {'Location': url_for('tasks.get_status', id=id)}
    return task.info

@celery.task(bind=True)
def download_media(self, media_info):
        with open("/app/transfer.txt", "w") as file:
            file.write("hi bob")
            file.write(str(self))
            file.write(str(media_info))
            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                file.write(f"Key: {k} - Value: {v}")
            server = plexsync.getServer(serverName)
            file.write(f"{str(server)}\n")
            file.write(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))

            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                file.write(f"{len(results)}")
            media = next(iter(results), None)
            file.write(f"{len(results)} Results found\n")
            file.write(f"sectionkey = {section.key} {section.type}\n")
            file.write(f"{media} Media\n")

            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                file.write(f"Key: {k} - Value: {v}\n")
            server = plexsync.getServer(serverName)
            file.write(f"{str(server)}\n")
            file.write(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))
            
            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                file.write(f"{len(results)}")
            media = next(iter(results), None)

            file.write(f"{len(results)} Results found\n")
            file.write(f"sectionkey = {section.key} {section.type}\n")
            file.write(f"{media} Media\n")
            for part in media.iterParts():
                url = media._server.url(
                    f"{part.key}?download=1", includeToken=True)

                token = media._server._token
                headers = {'X-Plex-Token': token}

                response = media._server._session.get(
                    url, headers=headers, stream=True)
                total = int(response.headers.get('content-length', 0))

                chunksize = 4096
                chunks = math.ceil(total / chunksize)
                currentChunk = 0

                with open(media_info["destination"], 'wb') as handle:
                    start = time.time()
                    status = {      "current": 0,
                                    "total": total,
                                    "start": start,
                                    "status": "starting"
                                }
                   # iterationElapsed = time.time() - status_info["start"]
                   # bytesPerSecond = math.floor(chunksize / iterationElapsed)
                   # etaSeconds = math.floor(int(status_info["bytes"]) / bytesPerSecond)
                    #status = {  "bytesPerSecond": bytesPerSecond,
                    #            "iterationElapsed": iterationElapsed,
                    #            "iterationStartTime": status_info["start"],
                    #            "etaSeconds": etaSeconds
                    #        }
                    meta = {'current': 0,
                            'status': "getting started",
                            'total': 1}

                    self.update_state(state='STARTING', meta=meta)

                    for chunk in response.iter_content(chunk_size=chunksize):
                        handle.write(chunk)
                                #iterationElapsed = time.time() - start
                                #bytesPerSecond = math.floor(chunksize / iterationElapsed)
                                #etaSeconds = math.floor(int(status_info["bytes"]) / bytesPerSecond)
                                #currentByte = currentChunk * chunksize
                                #status = {  "bytesPerSecond": bytesPerSecond,
                                #            "iterationElapsed": iterationElapsed,
                                #            "iterationStartTime": status_info["start"],
                                #            "etaSeconds": etaSeconds
                        meta = {        'current': currentChunk,
                                        'status': f"{round(currentChunk / total)}%",
                                        'total': chunks }

                        self.update_state(state='DOWNLOAD', meta=meta)
                        currentChunk += 1
                        totalTimeMS = time.time() - start
                        status = f'{media_info["title"]} Downloaded'
                        meta = {    'current': currentChunk,
                                        'status': status,
                                        'total': chunks,
                                        'totalTimeMS' : totalTimeMS
                           }
                        self.update_state(state='SUCCESS', meta=meta)

                    return meta

@celery.task()
def render_task(message):
        log.debug(f"Rendering {message}")
        server = message.get("server")
        section = message.get("section")
        guid = message.get("guid")

        plexsync = PlexSync()
        plexsync.getAccount()
        theirServer = plexsync.getServer(server)
        section = plexsync.getSection(theirServer, section)
        result = section.search(guid=guid).pop()
        template_data = plexsync.prepareMediaTemplate(result)

        with app.app_context():
            html = render_template('media.html', media=template_data)
            celery_log.debug("Emitting template_rendered") 
            socketio.emit('template_rendered', {'html': html}, namespace='/plexsync')

@celery.task()
def compare_task(message,bind=True, throw=True):
        plexsync = PlexSync()

        yourServerName = message.get("yourServer")
        theirServerName = message.get("theirServer")
        sectionName = message.get("section")

        plexsync = PlexSync()
        plexsync.getAccount()
        yourServer = plexsync.getServer(yourServerName)
        theirServer = plexsync.getServer(theirServerName)
        section = plexsync.getSection(theirServer, sectionName)

        yourLibrary = plexsync.getResults(yourServer, sectionName)
        theirLibrary = plexsync.getResults(theirServer, sectionName)
        results = plexsync.compareLibraries(yourLibrary, theirLibrary)
        guids = [x.guid for x in results]
        message = { "server" : theirServerName, "section" : sectionName, "items" : guids }
        logging.warning("Emitting comparison_done with {message}") 
        socketio.emit('comparison_done', {'message' : message}, namespace='/plexsync', broadcast=True)
        return message
