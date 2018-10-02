import requests
import threading
import time

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from .models import User
from .events import push_model
from . import db

main = Blueprint('main', __name__, template_folder='templates')


@main.before_app_first_request
def before_first_request():
    """Start a background thread that looks for users that leave."""
    def find_offline_users(app):
        with app.app_context():
            while True:
                users = User.find_offline_users()
                for user in users:
                    push_model(user)
                db.session.remove()
                time.sleep(5)

    if not current_app.config['TESTING']:
        thread = threading.Thread(target=find_offline_users,
                                  args=(current_app._get_current_object(),))
        thread.start()


#@main.before_app_request
#def before_request():

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
        plexsync = PlexSync()
        plexsync.getAccount()
        return redirect(url_for('main.home', _scheme='https', _external=True), code=303)
    except Exception as e:
       return json.dumps(str(e))

@main.route('/home', methods=['GET'])
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

@main.route('/pin/<string:pinId>', methods=['GET'])
def exchangePinForAuth(pinId):
   try:
        current_app.logger.debug(f"received pin id: {pinId}")
        headers = {'X-Plex-Client-Identifier': 'plexsync'}
        url = f"https://plex.tv/api/v2/pins/{pinId}.json"
        r = requests.get(url=url, headers=headers )
        token = r.json()['authToken']
        session['token'] = token
        current_app.logger.debug(f"Got auth token {token}")
        return redirect(url_for('main.home'))
   except KeyError:
        return redirect('/')

@main.route('/servers/<string:serverName>', methods=['GET','POST'])
def sections(serverName):
    current_app.logger.debug(f"routing for {serverName}")
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
