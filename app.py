#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from plexsync.plexsync import PlexSync

import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme'

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
        return redirect('https://plexsync.rtd3.me/home', code=303)
    
    except Exception as e:
        return json.dumps(str(e))

@app.route('/home', methods=['GET'])
def home():
   try:
        plexsync = PlexSync()
        plexAccount = plexsync.getAccount(session['username'], session['password'])
        servers = plexsync.getServers(plexAccount)
        sortedServers = sorted([server.name for server in servers])
        return render_template('home.html', server_list=sortedServers)   
   except KeyError:
        return redirect('https://plexsync.rtd3.me')

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

@app.route('/search/<string:theirServerName>/<int:sectionID>/<string:guid>', methods=['POST'])
def search(sectionID, guid):
    guid = urllib.unquote(guid).decode('utf-8')
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    theirServer = plexsync.getServer(theirServerName)
    section = theirServer.getSectionByID(sectionID)
    result = section.search(guid=guid)
    return json.dumps(result.title)


@app.route('/compare/<string:yourServerName>/<string:theirServerName>', methods=['GET'])
@app.route('/compare/<string:yourServerName>/<string:theirServerName>/<string:sectionName>', methods=['GET'])
def compare(yourServerName, theirServerName, sectionName=None):
    
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
        result_list = []
        for r in results:
                m = plexsync.getAPIObject(r)
                result_dict = {}
                result_dict['title'] = m.title
                print(m.overview)
                result_dict['overview'] = m.overview
                result_dict['sectionID'] = m.librarySectionID
                result_dict['year'] = m.year
                result_dict['guid'] = m.guid
                if len(m.images) > 0:
                    result_dict['image'] = m.images[0]['url'].replace("http", "https")
                result_dict['rating'] = m.rating
                result_list.append(result_dict)
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
    app.run(host='0.0.0.0', port=5000)
