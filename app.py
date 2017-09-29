#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify, g
from plexsync import PlexSync
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

@app.route('/servers', methods=['POST'])
def servers():
    session['username'] = request.form['username']
    session['password'] = request.form['password']

    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    servers = plexsync.getServers(plexAccount)
    sortedServers = sorted([server.name for server in servers])
    return json.dumps(sortedServers)
    

@app.route('/servers/<string:serverName>', methods=['GET','POST'])

def sections(serverName):
    print(f"routing for {serverName}")
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)

    sortedSections = sorted([section.title for section in sections])
    return json.dumps(sortedSections)

@app.route('/servers/<string:serverName>/<string:section>', methods=['GET','POST'])

def media(serverName, section):
    print(f"routing for {serverName} - {section}")
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    
    server = plexsync.getServer(serverName)
    media = plexsync.getMedia(server, section)

    sortedMedia = sorted([m.title for m in media])
    return json.dumps(sortedMedia)

if __name__ == '__main__':
    #https://stackoverflow.com/questions/26423984/unable-to-connect-to-flask-app-on-docker-from-host    
    app.run(host='0.0.0.0', port=5000)
