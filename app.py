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

    return render_template('servers.html',server_list=servers)
    #return redirect(url_for('message'))

@app.route('/servers/<string:serverName>', methods=['POST'])
def server(serverName):
    print(f"routing for {serverName}")
    plexsync = PlexSync()
    plexAccount = plexsync.getAccount(session['username'], session['password'])
    servers = plexsync.getServers(plexAccount)

    server = plexsync.getServer(serverName)
    sections = plexsync.getSections(server)
    return(json.dumps([s.title for s in sections]))
    
 #   return render_template('servers.html',server_list=servers, section_list=sections)
        
        

@app.route('/message')
def message():
    if not 'username' in session:
        return abort(403)
    return render_template('templates/message.html', username=session['username'], 
                                           message=session['message'])

if __name__ == '__main__':
    #https://stackoverflow.com/questions/26423984/unable-to-connect-to-flask-app-on-docker-from-host    
    app.run(host='0.0.0.0')
