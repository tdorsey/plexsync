import threading
import time

from flask import Blueprint, url_for, render_template, request, jsonify, current_app, url_for

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

#@main.route('/stats', methods=['GET'])
#def get_stats():
#    return jsonify({'requests_per_second': stats.requests_per_second()})
