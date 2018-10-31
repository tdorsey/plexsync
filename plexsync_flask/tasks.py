from flask import Blueprint, abort, g, request, current_app, render_template, jsonify
from .comparison_task import ComparisonTask


from plexsync import PlexSync

from celery.contrib.abortable import AbortableTask,AbortableAsyncResult
from celery import states, group
from celery.result import AsyncResult, GroupResult
from celery.utils.log import get_task_logger

import logging, urllib.parse

from progress.bar import Bar

from . import celery, socketio

from .utils import url_for, timing

import math, datetime, logging
tasks_bp = Blueprint('tasks', __name__)

log = logging.getLogger(__name__)

def dump(obj):
    if not obj:
        return None
    from pprint import pprint
    for attr in dir(obj):
        try:
            pprint("obj.{} = {}".format(attr, getattr(obj, attr)))
        except AttributeError:
            pprint("obj.{} = ?".format(attr))

def error_handler(self, uuid):
        result = AsyncResult(uuid)
        ex = result.get(propagate=False)
        logging.exception(
            f"Task {uuid} raised exception: {ex}\n{result.traceback}")

def updateProgress(pbar, extra):
    progress =  {
                    'current': pbar.index,
                    'total': pbar.max,
                    'remaining' : pbar.remaining,
                    'progress' : pbar.progress,
                    'eta': pbar.eta,
                    'percent' : pbar.percent,
                    'average' : pbar.avg }
    progress.update(extra)
    return progress


@tasks_bp.route('/<id>', methods=['GET', 'DELETE'])
def status(id):
    logger = logging.getLogger(__name__)
    from .wsgi_aux import app
    with app.app_context():
        task = AbortableAsyncResult(id, app=app.maybecelery)
        group_task = GroupResult.restore(id, app=app.maybecelery)
        if request.method == 'DELETE':
            task.abort()
            msg = f"Cancelling task {id}"
            logger.warning(msg)
            return jsonify(msg)
        else:
            if group_task:
                logger.debug(f"Group task: {group_task}")
                logger.debug(f"Children task count: { len(group_task.children) }")
            if task.state == 'PENDING':
                # job did not start yet
                response = {
                    'state': task.state,
                    'current': 0,
                    'total': 1,
                    'percent': 0,
                    'status': 'Pending...'
                }
            elif task.state == 'DOWNLOADING':
                response = {
                    'state': task.state,
                    'current': task.info.get('current', 0),
                    'total': task.info.get('total', 1),
                    'eta': task.info.get('eta', ''),
                    'bytesPerSecond': task.info.get('bytesPerSecond', ''),
                    'percent': task.info.get('percent', '')
             }
            if task.info and task.info.get('result'):
                response['result'] = task.info['result']
            elif task.state != 'FAILURE':
                logger.warning(f"task info {task.info}")
                response = { 'state': task.state, 'info' : task.info }
            else:
                # something went wrong in the background job
                response = {
                    'state': task.state,
                    'current': 1,
                    'total': 1,
                    'status': str(task.info),  # this is the exception raised
                 }
            return jsonify(response)

@celery.task(bind=True, base=AbortableTask)
def download_media(self, media_info):
    from .wsgi_aux import app
    with app.app_context():
            logger = get_task_logger(__name__)
            logger.setLevel(logging.DEBUG)   
            logger.info("Downloading {media_info}")
            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            logger.info(f"{media_info.items()}")
            server = plexsync.getServer(serverName)
            logger.info(f"{str(server)}\n")
            logger.info(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))

            if section.type == "show":
                result = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                result = section.search(guid=guid).pop()
            media = result
            logger.info(f"sectionkey = {section.key} {section.type}\n")
            logger.info(f"{media} Media\n")

            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            logger.info(f"{media_info.items()}")
            server = plexsync.getServer(serverName)
            logger.info(f"{str(server)}\n")
            logger.info(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))
            if section.type == "show":
                result = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                result = section.search(guid=guid).pop()
            media = result

            logger.info(f"sectionkey = {section.key} {section.type}\n")
            logger.info(f"{media} Media\n")
            for part in media.iterParts():
                url = media._server.url(
                    f"{part.key}?download=1", includeToken=True)

                token = media._server._token
                headers = {'X-Plex-Token': token}

                response = media._server._session.get(url, headers=headers, stream=True)
                total = int(response.headers.get('content-length', 0))

                chunksize=int(app.config['REQUESTS_CHUNKSIZE_BYTES'])
                chunks = math.ceil(total / chunksize)

                pbar = Bar('test', max=chunks)
                start_time = datetime.datetime.now()
                logger.info(f"Started at: {start_time}")

                progress = {'task': self.request.id, 'bytesPerSecond': 0, 'fileName' : media_info["destination"]}
                with open(media_info["destination"], 'wb') as handle:
                    for i, chunk in enumerate(response.iter_content(chunk_size=chunksize)):
                        if chunk:
                            handle.write(chunk)
                            if pbar.avg: #The average time, not size 
                                bytes_per_second = chunksize / pbar.avg
                            else:
                                bytes_per_second = 0
                            pbar.next()
                        if i % 10 == 0:
                            if self.is_aborted():
                                logger.info(f"Task {self.request.id} requested Abort. Removing {handle.filename}")
                                handle.close();
                                os.remove(handle.filename)
                        extra_info = {'bytesPerSecond': bytes_per_second }
                        progress.update(updateProgress(pbar, extra_info))
                        progress.update()
                        self.update_state(state='DOWNLOADING', meta=progress)
                pbar.finish()
                finish_time = datetime.datetime.now()
                elapsed = finish_time - start_time
                finish_seconds = elapsed.total_seconds()

                logger.info(f"Finished {media_info['title']} at: {finish_time} in {finish_seconds} seconds")

                self.update_state(state='SUCCESS', meta=progress)

                return progress


@tasks_bp.route('/render', methods=['POST'])
def render():
         json = request.get_json()
         serverName = json.get("server")
         sectionID = json.get("section")
         guids = json.get("guids")
         task = json.get("task")
         if guids:
            plexsync = PlexSync()
            plexsync.getAccount()
            template_data = []
            server = plexsync.getServer(serverName)
            section = server.library.sectionByID(sectionID)
         for guid in guids:
            guid = urllib.parse.unquote(guid)
            log.warning(f"guid: {guid}")
            if section.type == "show":
                result = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                result = section.search(guid=guid).pop()
            log.warning(f"Result found {result}" )
            template = plexsync.prepareMediaTemplate(result)
            template["task"] = task
            log.warning(f"Template found {template}" )
            template_data.append(template)
         log.warning(f"Template data {template_data}")
         html = render_template('media_in_progress.html', media_list=template_data)

         return html

@celery.task()
def emit_task(message):
    from .wsgi_aux import app
    with app.app_context():

        socketio.emit(message, namespace="/plexsync")



def update_and_emit(task, state, message, step=None, total_steps=None, message_level="info"):
    from .wsgi_aux import app
    with app.app_context():
        status_url = url_for('tasks.status', id=task.request.id)
        meta = {'status_url': status_url, 'level' : message_level,'current': step, 'total': total_steps, 'message': message}
        task.update_state(state=state, meta=meta)
        socketio.emit(state, meta, namespace='/plexsync')


@celery.task(bind=True, throw=True)
def compare_task(self, message):
    from .wsgi_aux import app
    with app.app_context():
        yourServerName = message.get("yourServer")
        theirServerName = message.get("theirServer")
        sectionName = message.get("section")
        currentStep = 1
        totalSteps = 8
        update_and_emit(self, "STARTING", str(f"Starting Comparison - This may take awhile"), step=1, total_steps=totalSteps)
        plexsync = PlexSync()
        plexsync.getAccount()
        update_and_emit(self, "CONNECTING", str(f"Connecting to {yourServerName}"), step=2, total_steps=totalSteps)
        yourServer = plexsync.getServer(yourServerName)
        update_and_emit(self, "CONNECTING", str(f"Connecting to {theirServerName}"), step=3, total_steps=totalSteps)
        theirServer = plexsync.getServer(theirServerName)
        update_and_emit(self, "SCANNING", str(f"Scanning {sectionName} on {yourServerName}"), step=4, total_steps=totalSteps)
        yourLibrary = plexsync.getResults(yourServer, sectionName)
        update_and_emit(self, "SCANNING", str(f"Scanning {sectionName} on {theirServerName}"), step=5, total_steps=totalSteps)
        theirLibrary = plexsync.getResults(theirServer, sectionName)
        update_and_emit(self, "COMPARING", str(f"Comparing {yourServerName} to {theirServerName}"), step=6, total_steps=totalSteps)
        results = plexsync.compareLibraries(yourLibrary, theirLibrary)
        guids = [x.guid for x in results]
        update_and_emit(self, "FINALIZING", str(f"Found {len(results)} new results on {theirServerName}"), message_level="SUCCESS", step=7, total_steps=totalSteps)
        message = { "server" : theirServerName, "section" : sectionName, "items" : guids }
        update_and_emit(self, "SUCCESS", message, message_level="SUCCESS", step=8, total_steps=totalSteps)
        socketio.emit('comparison_done', {'message' : message}, namespace='/plexsync')
        log = get_task_logger(__name__).warning("Comparison done")
        return message


def transfer_item(message):
    logger = logging.getLogger(__name__)
    from .wsgi_aux import app
    with app.app_context():

        serverName = message.get("server")
        sectionName = message.get("section")
        guid = message.get("guid")

        plexsync = PlexSync()

        media_info = plexsync.buildMediaInfo(serverName,sectionName,guid)
        
        items = []
        tasks = []
        for x in media_info:
            signature = download_media.s(x)
            logger.debug(f"signature {signature}")
            tasks.append(signature)

        group_result = group(tasks).apply_async()
        for x in group_result.children:
            items.append(x.id)
#        for x in tasks:
        logger.critical(f"group task: {group_result.id}") 
        response = {"message": "Transfer Started", "task":  group_result.id, "items" : items}
        logger.debug("Items: {items}")
        return response
