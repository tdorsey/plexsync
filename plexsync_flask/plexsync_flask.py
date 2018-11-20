import requests
import threading
import time
import urllib.parse
import logging

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from plexsync import PlexSync

from .tasks import compare_task, download_media

from .api.tasks import transfer_item
main = Blueprint('main', __name__, template_folder='templates')


@main.route('/')
def index():
    if not request.script_root:
        # this assumes that the 'index' view function handles the path '/'
        request.script_root = url_for('main.index', _external=True)
    return render_template('index.html')

@main.route('/login', methods=['POST'])
def login():
    session['username'] = request.form['username']
    session['password'] = request.form['password']

    try:
        plexsync = PlexSync.PlexSync()
        plexsync.getAccount()
        return redirect(url_for('main.home', _scheme='https', _external=True), code=303)
    except Exception as e:
        current_app.logger.exception(str(e), e)
        return jsonify(str(e))

@main.route('/home', methods=['GET'])
def home():
   try:
        token = session['token']
        session.permanent = True
        plexsync = PlexSync.PlexSync()
        if token:
            plexAccount = plexsync.getAccount(token=token)
        else:
            plexAccount = plexsync.getAccount()
        servers = plexsync.getServers(plexAccount)
        sortedServers = sorted([server.name for server in servers])
        return render_template('home.html', server_list=sortedServers)   
   except KeyError:
        return redirect('/')

@main.route('/pin/redirect_to/<string:client>/<int:pin>', methods=['GET'])
def getRedirectURL(client,pin):
    forwardURL = url_for('main.exchangePinForAuth', clientId=client, pinId=pin, _scheme='https', _external=True )
    current_app.logger.debug(f"Got forwardURL {forwardURL}")
    return jsonify(forwardURL)

@main.route('/pin/<string:clientId>/<string:pinId>', methods=['GET'])
def exchangePinForAuth(clientId, pinId):
   try:
        current_app.logger.debug(f"received pin id: {pinId}")
        headers = {'X-Plex-Client-Identifier': clientId}
        url = f"https://plex.tv/api/v2/pins/{pinId}.json"
        r = requests.get(url=url, headers=headers )
        token = r.json()['authToken']
        session['token'] = token
        current_app.logger.debug(f"Got auth token {token}")
        return redirect(url_for('main.home'))
   except KeyError:
        
        current_app.logger.exception(f"An error occurred signing in to Plex: {r.json()}")
        return jsonify(r.json()['errors'].pop()['message'])

@main.route('/servers/<string:serverName>', methods=['GET','POST'])
def sections(serverName):
    current_app.logger.debug(f"routing for {serverName}")
    plexsync = PlexSync.PlexSync()
    plexsync.getAccount()
    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)

    section_list = []
    
    for section in sections:
        result = {"id": section.key, "name": section.title, "type": section.type}
        section_list.append(result)
        sortedSections = sorted(section_list,key=lambda s: s.get("name"))
    with current_app.app_context():
        return jsonify(sortedSections)

@main.route('/servers/<string:serverName>/<string:section>', methods=['GET','POST'])
def media(serverName, section):
    current_app.logger.debug(f"routing for {serverName} - {section}")
    plexsync = PlexSync.PlexSync()
    plexsync.getAccount()
    
    server = plexsync.getServer(serverName)
    results = plexsync.getResults(server, section)

    sortedResults = sorted([r.title for r in results])
    with current_app.app_context():
        return jsonify(sortedResults)

@main.route('/search', methods=['POST'])
def search():
    guid = request.form['guid']
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync = PlexSync.PlexSync()
    plexsync.getAccount()
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    m = plexsync.getAPIObject(result)
    response = plexsync.sendMediaToThirdParty(m)
    return render_template('third_party.html', message=response)

@main.route('/download', methods=['POST'])
def download():
    guid = request.form['guid']
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync = PlexSync.PlexSync()
    plexsync.getAccount()
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    result.download()

@main.route('/transfer', methods=['POST'])
def transfer():
    try:
        server = request.form['server']
        sectionID = request.form['section']
        guid = request.form['guid']
        guid = urllib.parse.unquote(guid)
        plexsync = PlexSync.PlexSync()
        plexsync.getAccount()

        ownedServers = plexsync.getOwnedServers()
        currentUserServer = session['yourServer']
        current_app.logger.debug(f"ownedServers {ownedServers}")
        current_app.logger.debug(f"currentServer {currentUserServer}")
        authorized = False
        for s in ownedServers:
            if s.friendlyName == currentUserServer:
                authorized = True
            theirServer = plexsync.getServer(server)
            section = theirServer.library.sectionByID(sectionID)
            result = section.search(guid=guid).pop()
        if authorized:
            current_app.logger.debug(f"authorized")
            item = { "server" : theirServer.friendlyName,
                     "section" : section.title,
                     "guid" : guid  }

            response = transfer_item(item)
            return jsonify(response)

        else:
                current_app.logger.debug(f"not authorized")
                msg = f"Not authorized to transfer {result.title} to {currentUserServer}"
                status = 403
                response =  jsonify(message= {"text" : msg, "severity" : "danger" }, status=status)
                response.status_code = status
                return response
    except Exception as e:
                    current_app.logger.exception(f"Exception {e}")
                    status = 500
                    response =  jsonify(message= {"text" : str(e), "severity" : "danger" }, status=status)
                    response.status_code = status
                    return jsonify(str(e))

@main.route('/item/<string:serverName>/<string:sectionName>/<path:guid>', methods=['GET'])
def renderSingleItemPath(serverName, sectionName, guid):
            current_app.logger.info(f"Rendering GUID {guid}")
            serverName = urllib.parse.unquote(serverName)
            sectionName = urllib.parse.unquote(sectionName)
            guid = urllib.parse.unquote(guid)
            plexsync = PlexSync.PlexSync()
            plexsync.getAccount()
            server = plexsync.getServer(serverName)
            section = plexsync.getSection(server, sectionName)
            result = section.search(guid=guid).pop()
            m = plexsync.prepareMediaTemplate(result)
            return render_template('media.html', media=m)

@main.route('/compare/<string:yourServerName>/<string:theirServerName>', methods=['GET'])
@main.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:section>', methods=['GET'])
@main.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:sectionKey>', methods=['GET'])
def compare(yourServerName, theirServerName, sectionKey=None):
    try:
        with current_app.app_context():
            plexsync = PlexSync.PlexSync()
            plexsync.getAccount()
            theirServer = plexsync.getServer(theirServerName)

            section = plexsync.getSection(theirServer, sectionKey)
            sectionName = section.title

            session['yourServer'] = yourServerName
            message = { "yourServer" : yourServerName,
                    "theirServer" : theirServerName,
                    "section" : sectionName  }

            current_app.logger.warning(f"{message}")
            signature = compare_task.s()
            task = signature.apply_async(args=[message])
            current_app.logger.debug(f" result backend {task.backend}")
            current_app.logger.debug(f"Compare Task: {task} ")
      
            message["task"] = task.id
            status_url = url_for('api.status', _scheme='https', _external=True, id=task.id)
            message["status_url"] = status_url
            return jsonify(message)

    except Exception as e:
        with current_app.app_context():
            current_app.logger.exception(e)
            response = jsonify(str(e))
            response.status_code = 500
            return response
#    if as_json():
 #   return jsonify(result_list)
  #  else:
 #   return render_template('media.html', media=result_list)

