#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify
from plexsync import PlexSync
app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme'


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

@app.route('/servers/<string:server>', methods=['POST'])
def server(server):
    session['server'] = request.form['server']
    return jsonify("whee")
        
        

@app.route('/message')
def message():
    if not 'username' in session:
        return abort(403)
    return render_template('templates/message.html', username=session['username'], 
                                           message=session['message'])

if __name__ == '__main__':
    app.run()
