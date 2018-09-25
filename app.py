#!/usr/bin/python3

from datetime import timedelta
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from flask_socketio import SocketIO, emit
from plexsync.plexsync import PlexSync

from plexsync.tasks import *  

import json
import urllib.parse
import logging
import requests
import traceback
import sys

app = Flask(__name__)

app.config['SECRET_KEY'] = 'changeme'
app.config['LOGGER_NAME'] = 'plexsync'
app.config['SERVER_NAME'] = 'ps.rtd3.me'
app.config['DEBUG'] = False
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=5)
app.config['CELERY_BROKER_URL'] = 'pyamqp://rabbitmq:rabbitmq@rabbitmq'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

socketio = SocketIO(app)

def as_json():

    if  request.args.get('json', None):
        return True


# If content type is application/json, return json, else render the template
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']



plexsync = None

@app.route('/')
def index():
    if not request.script_root:
        # this assumes that the 'index' view function handles the path '/'
        request.script_root = url_for('index', _external=True)
    return render_template('index.html')

@app.route('/notify', methods=['GET', 'POST'])
def notify():
        app.logger.debug("***notify hit***")
        app.logger.debug(f"form data: {request.form}"  )
        fields = [k for k in request.form]                                      
        values = [request.form[k] for k in request.form]
        data = dict(zip(fields, values))
        socketio.emit("comparison_done", {'message' : data }, namespace='/plexsync')
        app.logger.debug(f"{data}")
        return jsonify(data) 

@app.route('/login', methods=['POST'])
def login():
    session['username'] = request.form['username']
    session['password'] = request.form['password']

    try:
        plexsync = PlexSync()
        plexsync.getAccount()
        return redirect(url_for('home', _scheme='https', _external=True), code=303)
    except Exception as e:
       return json.dumps(str(e))

@app.route('/home', methods=['GET'])
def home():
   try:
        token = session['token']
        session.permanent = True
        plexsync = PlexSync()
        if token:
            plexAccount = plexsync.getAccount(token=token)
        else:
            plexAccount = plexsync.getAccount()
        servers = plexsync.getServers(plexAccount)
        sortedServers = sorted([server.name for server in servers])
        return render_template('home.html', server_list=sortedServers)   
   except KeyError:
        return redirect('/')

@app.route('/pin/<string:pinId>', methods=['GET'])
def exchangePinForAuth(pinId):
   try:
     app.logger.debug(f"received pin id: {pinId}")
     headers = {'X-Plex-Client-Identifier': 'plexsync'}
     url = f"https://plex.tv/api/v2/pins/{pinId}.json"
     r = requests.get(url=url, headers=headers )
     token = r.json()['authToken']
     session['token'] = token
     app.logger.debug(f"Got auth token {token}")
     return redirect(url_for('home'))
   except KeyError:
        return redirect('/')

@app.route('/servers/<string:serverName>', methods=['GET','POST'])
def sections(serverName):
    app.logger.debug(f"routing for {serverName}")
    plexsync = PlexSync()
    plexsync.getAccount()
    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)

    section_list = []
    
    for section in sections:
        result = {"id": section.key, "name": section.title, "type": section.type}
        section_list.append(result)
        sortedSections = sorted(section_list,key=lambda s: s.get("name"))
    return json.dumps(sortedSections, ensure_ascii=False)

@app.route('/servers/<string:serverName>/<string:section>', methods=['GET','POST'])

def media(serverName, section):
    app.logger.debug(f"routing for {serverName} - {section}")
    plexsync = PlexSync()
    plexsync.getAccount()
    
    server = plexsync.getServer(serverName)
    results = plexsync.getResults(server, section)

    sortedResults = sorted([r.title for r in results])
    return json.dumps(sortedResults, ensure_ascii=False)

@app.route('/search', methods=['POST'])
def search():
    guid = request.form['guid']
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync = PlexSync()
    plexsync.getAccount()
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    m = plexsync.getAPIObject(result)
    response = plexsync.sendMediaToThirdParty(m)
    return render_template('third_party.html', message=response)

@app.route('/download', methods=['POST'])
def download():
    guid = request.form['guid']
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync = PlexSync()
    plexsync.getAccount()
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    result.download()

@app.route('/transfer', methods=['POST'])
def transfer():
    try:
        server = request.form['server']
        sectionID = request.form['section']
        guid = request.form['guid']
        guid = urllib.parse.unquote(guid)
        plexsync = PlexSync()
        plexsync.getAccount()

        ownedServers = plexsync.getOwnedServers()
        currentUserServer = session['yourServer']
        app.logger.debug(f"ownedServers {ownedServers}")
        app.logger.debug(f"currentServer {currentUserServer}")
        authorized = False
        for s in ownedServers:
            if s.friendlyName == currentUserServer:
                app.logger.debug(f"authorized")
                authorized = True

            theirServer = plexsync.getServer(server)
            section = theirServer.library.sectionByID(sectionID)
            result = section.search(guid=guid).pop()
        if authorized:
            app.logger.debug("building task")
            try:
                transferred = plexsync.transfer(theirServer.friendlyName, sectionID, guid)
                app.logger.debug(f"Transferred Results {transferred} Len: {len(transferred)}")
            except Exception as e:
                app.logger.exception(f"Exception {e}")
                status = 500
                response =  jsonify(message= {"text" : str(e), "severity" : "danger" }, status=status)
                response.status_code = status
                return response
            
            msg = f"Transferring {len(transferred)} items to {currentUserServer}"
            status = 202
            response = jsonify(message = { "text" : msg, "severity" : "success" }, result=transferred, status=status)
            response.status_code = status
            return response
        
        else:
            app.logger.debug(f"not authorized")
            msg = f"Not authorized to transfer {result.title} to {currentUserServer}"
            status = 403
            response =  jsonify(message= {"text" : msg, "severity" : "danger" }, status=status)
            response.status_code = status
            return response
    except Exception as e:
        app.logger.exception(f"Exception {e}")
        status = 500
        response =  jsonify(message= {"text" : str(e), "severity" : "danger" }, status=status)
        response.status_code = status
        return response
        
@app.route('/compare/<string:yourServerName>/<string:theirServerName>', methods=['GET'])
@app.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:section>', methods=['GET'])
@app.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:sectionKey>', methods=['GET'])
def compare(yourServerName, theirServerName, sectionKey=None):
    try:
        plexsync = PlexSync()
        plexsync.getAccount()
        yourServer = plexsync.getServer(yourServerName)
        theirServer = plexsync.getServer(theirServerName)

        section = plexsync.getSection(theirServer, sectionKey)
        sectionName = section.title

        session['yourServer'] = yourServerName
        message = { "yourServer" : yourServerName,
                    "theirServer" : theirServerName,
                    "section" : sectionName  }
        app.logger.debug("compare route hit")


        app.logger.warning(f"{message}")
        signature = compare_task.s()
        task = signature.apply_async(args=[message])
        app.logger.debug(f" result backend {task.backend}")
        app.logger.debug(f"Compare Task: {task} ")
      
        message["task"] = task.id
        return jsonify(message)

    except Exception as e:
        app.logger.exception(e)
        response = jsonify(str(e))
        response.status_code = 500
        return response
    #if as_json():
    #return jsonify(result_list)
    #else:
     #   return render_template('media.html', media=result_list)

@app.route('/compareResults/<string:yourServerName>/<string:theirServerName>/<string:sectionName>', methods=['GET'])
def compareResults(yourServerName, theirServerName, sectionName=None):

    plexsync = PlexSync()
    plexsync.getAccount(session['username'], session['password'])
    sectionsToCompare = []

    if not sectionName:
        settings = plexsync.getSettings()
        sectionsToCompare = settings.get('sections', 'sections').split(",")
    else:
        sectionsToCompare.append(sectionName)

    yourServer = plexsync.getServer(yourServerName)
    theirServer = plexsync.getServer(theirServerName)

    for section in sectionsToCompare:
        yourLibrary = plexsync.getResults(yourServer, section)
        theirLibrary = plexsync.getResults(theirServer, section)

        results = plexsync.compareLibrariesAsResults(yourLibrary, theirLibrary)

        app.logger.debug(f"{section} {len(yourLibrary)} in yours {len(theirLibrary)} in theirs")
        app.logger.debug(f"{len(results)} your diff")

    return jsonify(results)

@app.route('/task/<task_id>')
def taskstatus(task_id):
    task = getTaskProgress(task_id)
    return jsonify(task)

def ack():
    app.logger.warning('message was received!')

def render_and_emit(message):
    
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

    socketio.emit('template_rendered', {'html': html}, namespace='/plexsync')

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

@socketio.on('comparison_done', namespace='/plexsync')
def plexsync_message(message):
   app.logger.debug(f"comparison re emitted {message}")


@socketio.on('render_template', namespace='/plexsync')
def plexsync_message(message):
    app.logger.info(f"rendering template for {message.get('guid')}")
    app.logger.debug(f"message: {message}")

    plexsync = PlexSync()
    plexsync.render(message)
    #socketio.start_background_task(render_and_emit, message)

@socketio.on('broadcast', namespace='/plexsync')
def plexsync_broadcast(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect', namespace='/plexsync')
def plexsync_connect():
    app.logger.info('Client connected')
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/plexsync')
def plexsync_disconnect():
    app.logger.info('Client disconnected')


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        include='plexsync.tasks'
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            kwargs={}
            kwargs['exc_info']=exc
            log.error('Task % failed to execute', task_id, **kwargs)
            super().on_failure(exc, task_id, args, kwargs, einfo)

        def after_return(self, status, retval, task_id, args, kwargs, einfo):
            app.logger.debug(f"after return {self}")
            url = 'http://localhost:5000/notify'
            data = {'clientid': kwargs['clientid'], 'result': retval}
            requests.post(url, data=data)

    celery.Task = ContextTask
    return celery

if __name__ == '__main__':
    celery = make_celery(app)
    #https://stackoverflow.com/questions/26423984/unable-to-connect-to-flask-app-on-docker-from-host
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)

    socketio.run(app, host='0.0.0.0', port=5000)

