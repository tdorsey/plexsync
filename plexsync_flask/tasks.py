from flask import Blueprint, abort, g, request, current_app, render_template


from plexsync import PlexSync

from celery import states
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from logging import getLogger

from . import celery, socketio

from .utils import url_for

import math, time

tasks_bp = Blueprint('tasks', __name__)

def error_handler(self, uuid):
        result = AsyncResult(uuid)
        ex = result.get(propagate=False)
        logging.exception(
            f"Task {uuid} raised exception: {ex}\n{result.traceback}")

@tasks_bp.route('/<id>', methods=['GET'])
def status(id):
    from .wsgi_aux import app
    with app.app_context():    
        task = AsyncResult(id)
        if task.state == 'PENDING':
            # job did not start yet
            response = {
                'state': task.state,
                'current': 0,
                'total': 1,
                'status': 'Pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', '')
             }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            # something went wrong in the background job
            response = {
                'state': task.state,
                'current': 1,
                'total': 1,
                'status': str(task.info),  # this is the exception raised
             }
        return jsonify(response)

@tasks_bp.route('/status/<id>', methods=['GET'])
def get_status(id):
    """
    Return status about an asynchronous task. If this request returns a 202
    status code, it means that task hasn't finished yet. Else, the response
    from the task is returned.
    """
    task = AsyncResult(id)
    if task.state == states.PENDING:
        abort(404)
    if task.state == states.RECEIVED or task.state == states.STARTED:
        return '', 202, {'Location': url_for('tasks.get_status', id=id)}
    return task.info

@celery.task(bind=True)
def download_media(self, media_info):
    from .wsgi_aux import app
    with app.app_context():
            logger = get_task_logger(__name__)
            logger.info("Downloading {media_info}")
            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                logger.info(f"Key: {k} - Value: {v}")
            server = plexsync.getServer(serverName)
            logger.info(f"{str(server)}\n")
            logger.info(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))

            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                logger.info(f"{len(results)}")
            media = next(iter(results), None)
            logger.info(f"{len(results)} Results found\n")
            logger.info(f"sectionkey = {section.key} {section.type}\n")
            logger.info(f"{media} Media\n")

            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                logger.info(f"Key: {k} - Value: {v}\n")
            server = plexsync.getServer(serverName)
            logger.info(f"{str(server)}\n")
            logger.info(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))
            
            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                logger.info(f"{len(results)}")
            media = next(iter(results), None)

            logger.info(f"{len(results)} Results found\n")
            logger.info(f"sectionkey = {section.key} {section.type}\n")
            logger.info(f"{media} Media\n")
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
                    status_info = {      "current": 0,
                                    "total": total,
                                    "start": start,
                                    "status": "starting"
                                }
                    iterationElapsed = time.time() - status_info["start"]
                    bytesPerSecond = math.floor(chunksize / iterationElapsed)
                    etaSeconds = math.floor(int(status_info["total"]) / bytesPerSecond)
                    status = {  "bytesPerSecond": bytesPerSecond,
                               "iterationElapsed": iterationElapsed,
                                "iterationStartTime": status_info["start"],
                                "etaSeconds": etaSeconds
                            }
                    meta = {'current': 0,
                            'status': status,
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

# @celery.task()
# def render_task(message):
#         log.debug(f"Rendering {message}")
#         server = message.get("server")
#         section = message.get("section")
#         guid = message.get("guid")

#         plexsync = PlexSync()
#         plexsync.getAccount()
#         theirServer = plexsync.getServer(server)
#         section = plexsync.getSection(theirServer, section)
#         result = section.search(guid=guid).pop()
#         template_data = plexsync.prepareMediaTemplate(result)

#         with app.app_context():
#             html = render_template('media.html', media=template_data)
#             celery_log.debug("Emitting template_rendered") 
#             socketio.emit('template_rendered', {'html': html}, namespace='/plexsync')

@celery.task()
def emit_task(message):
    from .wsgi_aux import app
    with app.app_context():
        socketio.emit(message, namespace="/plexsync")

@celery.task()
def compare_task(message,bind=True, throw=True):
    from .wsgi_aux import app
    with app.app_context():
        yourServerName = message.get("yourServer")
        theirServerName = message.get("theirServer")
        sectionName = message.get("section")

        plexsync = PlexSync()
        plexsync.getAccount()
        yourServer = plexsync.getServer(yourServerName)
        theirServer = plexsync.getServer(theirServerName)

        yourLibrary = plexsync.getResults(yourServer, sectionName)
        theirLibrary = plexsync.getResults(theirServer, sectionName)
        results = plexsync.compareLibraries(yourLibrary, theirLibrary)
        guids = [x.guid for x in results]
        message = { "server" : theirServerName, "section" : sectionName, "items" : guids }
        socketio.emit('comparison_done', {'message' : message}, namespace='/plexsync', broadcast=True)
        return message



@celery.task(bind=True, throw=True)
def transfer_task(self, message):
    logger = getLogger("plexsync")
    logger.info(f"Starting Task {self.name}: {self.request.id} in Backend {self.backend}")
    from .wsgi_aux import app
    with app.app_context():

        serverName = message.get("server")
        sectionName = message.get("section")
        guid = message.get("guid")

        plexsync = PlexSync()

        media_info = plexsync.buildMediaInfo(serverName,sectionName,guid)
        
        response = {"message": "Transfer Started"}
        items = []
        for x in media_info:
            signature = download_media.s()
            download_task = signature.apply_async(args=[x])
            items.append({'task': download_task.id})
        response["items"] = items
        return response
