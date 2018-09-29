#!/usr/bin/python3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from plexsync import PlexSync

import json
import urllib.parse
import logging
import requests
import traceback
import sys

from plexsync_flask import create_app
app = create_app() 


#celery = make_celery(aapp, main=True)
#socketio = make_socketio(app, main=True)

plexsync = None

def as_json():
# If content type is application/json, return json, else render the template
    # best = request.accept_mimetypes \
    #     .best_match(['application/json', 'text/html'])
    # return best == 'application/json' and \
    #     request.accept_mimetypes[best] > \
    #     request.accept_mimetypes['text/html']
    if  request.args.get('json', None):
         return True

@app.route('/')
def index():
    if not request.script_root:
        # this assumes that the 'index' view function handles the path '/'
        request.script_root = url_for('index', _external=True)
    return render_template('index.html')

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
    task = tasks.getTaskProgress(task_id)
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

    #socketio.emit('template_rendered', {'html': html}, namespace='/plexsync')




if __name__ == '__main__':
    #https://stackoverflow.com/questions/26423984/unable-to-connect-to-flask-app-on-docker-from-host
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)


    socketio = SocketIO(app=app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
#This hangs serving the index page
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)

#This serves with eventlet warnings, but can't find the templates
#    app.run(host='0.0.0.0', port=5000)

