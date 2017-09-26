#!/usr/bin/python3

from pick import Picker
from plexapi.myplex import MyPlexAccount

import getpass
import re
import enum
import requests
import urllib

from apiobject import APIObject
from base import *
from thirdparty import ThirdParty
from thirdparty import ThirdPartyService
from plexsync import PlexSync

def _selectAll(picker):
    print("selecting all")
    return None

def chooseMedia(media: set):
    _title = 'Please select the media you want to sync (press SPACE to select, ENTER to continue):'
    #convert our media set to a list so we can match the selected indexes to the media
    media_list = sorted(media,  key=lambda m: m.title)
    _options = [m.title for m in media_list]
    picker = Picker(_options, _title, multi_select=True)
    selected_items = picker.start()
    wantedMedia = []
    for s in selected_items:
        media_index = s[1]
        wantedMedia.append(media_list[media_index])    
    return wantedMedia

settings = getSettings()
plexsync = PlexSync()

username =  input("MyPlex username:") or settings.get('auth', 'myplex_username')
password = getpass.getpass("MyPlex password:") or settings.get('auth', 'myplex_password')

if username and password:
    account = plexsync.getAccount(username, password)
else:
    print("Set a username and passsword in the config file")
    exit(1)

tv_quality_profile =  input("TV Quality Profile:") or settings.get('sonarr', 'quality_profile')
movie_quality_profile =  input("Movie Quality Profile:") or settings.get('radarr', 'quality_profile')


plexsync.getServers()

your_server_name =  input("Your server: ") or settings.get('servers', 'yours')
their_server_name = input("Their server: ") or settings.get('servers', 'theirs')

# returns a PlexServer instance
your_server = account.resource(your_server_name).connect()
# returns a PlexServer instance
their_server = account.resource(their_server_name).connect()

sections = settings.get('sections', 'sections').split(",")
for section in sections:
    your_media = plexsync.getMedia(your_server, section)
    their_media = plexsync.getMedia(their_server, section)

    their_new_media = their_media - your_media
    your_new_media = your_media - their_media

    #printMedia(their_new_media, section)

    wantedMedia = chooseMedia(their_new_media)
    plexsync.sendMediaToThirdParty(wantedMedia)
