#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, abort, session
from plexsync import PlexSync
app = Flask(__name__)
app.config['SECRET_KEY'] = 'changeme'

@app.route('/')
def index():
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

@app.route('/message')
def message():
    if not 'username' in session:
        return abort(403)
    return render_template('templates/message.html', username=session['username'], 
                                           message=session['message'])

if __name__ == '__main__':
    app.run()
