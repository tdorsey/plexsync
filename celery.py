
from __future__ import absolute_import, unicode_literals

from plexsync.plexsync import PlexSync

import json
import logging
import requests

from plexsync-flask import celery, make_celery
from .factory import make_socketio, get_logger

flask_app = create_app(main=False)
celery = make_celery(flask_app, main=False)
socketio = make_socketio(flask_app, main=False)
log = get_logger(flask_app)

def getTaskProgress(taskID):
      task = celery.AsyncResult(taskID)
      log.warning(f"Retrieved task {task}")
      if task.state == 'PENDING':
               # job did not start yet
               response = {
               'state': task.state,
               'current': 0,
               'total': 1,
               'status': 'Pending...'
                }
      if task.state == 'FAILURE':
               # job did not start yet
               response = {
               'state': task.state,
               'current': 1,
               'total': 1,
               'status': str(task.info)
                }
      elif task.state != 'FAILURE' :
        if not task.info:
           response = { 'state': task.state,
                        'status' : "No task info available"   }
        else:
                response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', '')
                }
        if task.info:
            response['result'] = task.info.get('result', None)
      return response

def getGroupProgress(taskID):
        task_group = celery.GroupResult.restore(taskID)
        with open("/app/info.txt", "w") as file:

            file.write(f"{task_group}\n\n")

            group_total = 0
            group_current = 0
            for t in task_group.results:
#                file.write(f"Task ID: {t.id} - task state: {t.state}\n\n")
#                file.write(f"task info: {t.info}\n\n")
                status = str(t.info) or t.state

                if t.state in ["FAILURE", "PENDING"]:
                    meta = {'current': 0, 'status': status, 'total': 1}
                    continue
                else:
                    task_current = t.info.get('current', 0)
                    task_total = t.info.get('total', 1)

                    group_current += task_current
                    group_total += task_total
                    file.write(f"@@@{group_current}@@@\n***{group_total}***\n")

                    meta = {'current': group_current,
                            'status': 'PROGRESS',
                            'total': group_total}
                    file.write(f'{t.id}-{t.state.upper()}: {meta["current"]} of {meta["total"]}: {int(meta["current"] / meta["total"])}\n')
            return meta 

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
 
#        rabbit_queue = 'amqp://rabbitmq:rabbitmq@rabbitmq'
#        rabbit_queue2 = 'amqp://rabbitmq:rabbitmq@rabbitmq'
#        redis_queue = 'redis://redis:6379/4'
#        rabbit_queue3 = 'amqp://compare:compare@rabbitmq/compare'
#        threaded_socket = SocketIO(logger=True, async_mode='threading', engineio_logger=True,message_queue=rabbit_queue)
#        eventlet_socket = SocketIO(logger=True, async_mode='eventlet', engineio_logger=True,message_queue=rabbit_queue)
#        threaded_socket.emit('comparison_done', {'message' : 'test'}, namespace='/plexsync', broadcast=True)
#        eventlet_socket.emit('comparison_done', {'message' : 'test'}, namespace='/plexsync', broadcast=True)
#        threaded_socket.emit('comparison_done', 'test', namespace='/plexsync')
#        eventlet_socket.emit('comparison_done', 'test', namespace='/plexsync')

      
