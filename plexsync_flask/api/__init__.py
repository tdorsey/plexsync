from flask import Blueprint
from plexsync import PlexSync

api = Blueprint('api', __name__)
plexsync = PlexSync()

from . import  media, servers, transfer, auth, tasks

