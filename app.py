#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from plexsync.plexsync import PlexSync

import json
import urllib.parse
import logging
import sys

app = Flask(__name__)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'changeme'
app.config['LOGGER_NAME'] = 'plexsync'


def as_json():
''' If content type is application/json, return json, else render the template
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    rtn =  best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']
    return rtn

plexsync = None

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

    plexsync = PlexSync()
    try:
        plexAccount = plexsync.getAccount(session['username'], session['password'])
        return redirect(url_for('home', _scheme='https', _external=True), code=303)
    except Exception as e:
        return json.dumps(str(e))

@app.route('/home', methods=['GET'])
def home():
   try:
        plexsync = PlexSync()
        plexAccount = plexsync.getAccount(username=session['username'], password=session['password'])
        servers = plexsync.getServers(plexAccount)
        sortedServers = sorted([server.name for server in servers])
        return render_template('home.html', server_list=sortedServers)   
   except KeyError:
        return redirect('/')

@app.route('/servers/<string:serverName>', methods=['GET','POST'])
def sections(serverName):
    print(f"routing for {serverName}")
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)

    sortedSections = sorted([section.title for section in sections])
    return json.dumps(sortedSections, ensure_ascii=False)

@app.route('/servers/<string:serverName>/<string:section>', methods=['GET','POST'])

def media(serverName, section):
    print(f"routing for {serverName} - {section}")
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    
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
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    m = plexsync.getAPIObject(result)
    response = plexsync.sendMediaToThirdParty(m)
    return render_template('third_party.html', message=response)

@app.route('/download', methods=['POST'])
def download():
    guid = urllib.parse.unquote(guid)
    server = request.form['server']
    section = request.form['section']
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    theirServer = plexsync.getServer(server)
    section = theirServer.library.sectionByID(section)
    result = section.search(guid=guid).pop()
    result.download()

@app.route('/transfer', methods=['POST'])
def transfer():
    try:
        server = request.form['server']
        section = request.form['section']
        guid = request.form['guid']
        guid = urllib.parse.unquote(guid)
        plexsync = PlexSync()
        plexAccount = plexsync.getAccount(session['username'], session['password'])

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
            section = theirServer.library.sectionByID(section)
            result = section.search(guid=guid).pop()
            key = result.ratingKey 
        if authorized:
            app.logger.debug("building task") 
            try:
              task = plexsync.transfer2.delay(theirServer.friendlyName, guid)
              task.get(propagate=True)
            except Exception as e:
              return json.dumps(str(e))

            msg = f"Transferring {result.title} to {currentUserServer}"
            return json.dumps(msg)
        else:
            app.logger.debug(f"not authorized")
            msg = f"Not authorized to transfer {result.title} to {currentUserServer}"
            return json.dumps(msg)
    except Exception as e:
        return json.dumps(str(e))

@app.route('/compare/<string:yourServerName>/<string:theirServerName>', methods=['GET'])
@app.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:sectionName>', methods=['GET'])
def compare(yourServerName, theirServerName, sectionName=None):
    try:
        plexsync = PlexSync()
        plexAccount = plexsync.getAccount(session['username'], session['password'])
        sectionsToCompare = []

        if not sectionName:
            settings = plexsync.getSettings()
            sectionsToCompare = settings.get('sections', 'sections').split(",")
        else:
            sectionsToCompare.append(sectionName)

        yourServer = plexsync.getServer(yourServerName)
        session['yourServer'] = yourServerName
        theirServer = plexsync.getServer(theirServerName)

        for section in sectionsToCompare:
            yourLibrary = plexsync.getResults(yourServer, section)
            theirLibrary = plexsync.getResults(theirServer, section)
            results = plexsync.compareLibrariesAsResults(yourLibrary, theirLibrary)

            app.logger.debug(f"{section} {len(yourLibrary)} in yours {len(theirLibrary)} in theirs")
            app.logger.debug(f"{len(results)} your diff")
            result_list = []

            for r in results:

                m = plexsync.getAPIObject(r)

                result_dict = {}
                result_dict['title'] = m.title
                result_dict['downloadURL'] = m.downloadURL
                result_dict['overview'] = m.overview
                result_dict['sectionID'] = m.librarySectionID
                result_dict['year'] = m.year
                result_dict['guid'] = urllib.parse.quote_plus(m.guid)
                result_dict['server'] = theirServer.friendlyName
                if m.image and len(m.image) > 0:
                    result_dict['image'] = m.image
                result_dict['rating'] = m.rating
                result_list.append(result_dict)
    except Exception as e:
          return json.dumps(str(e))
    if as_json():
        return jsonify(result_list)
    else:
        return render_template('media.html', media=result_list)
    

@app.route('/compareResults/<string:yourServerName>/<string:theirServerName>/<string:sectionName>', methods=['GET'])
def compareResults(yourServerName, theirServerName, sectionName=None):

    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
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

        print(f"{section} {len(yourLibrary)} in yours {len(theirLibrary)} in theirs")
        print(f"{len(results)} your diff")

        return json.dumps([r.title for r in results], ensure_ascii=False)

if __name__ == '__main__':
    #https://stackoverflow.com/questions/26423984/unable-to-connect-to-flask-app-on-docker-from-host    
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)

    app.run(host='0.0.0.0', port=5000)
    
