#!/usr/bin/python3

from plexapi.myplex import MyPlexAccount

import getpass
import re
import enum
import requests
import urllib

from apiobject import APIObject
from base import *

def printHeaderLine():
    print('*******************')

def getServers(account):
    resources = account.resources()
    servers = filter(lambda x: x.provides == 'server', account.resources())
    for s in servers:
        print(s.name)


def dump(obj):
    for attr in dir(obj):
        if hasattr(obj, attr):
            print("obj.%s = %s" % (attr, getattr(obj, attr)))


def getMedia(server, section):
    results = server.library.section(section).search()
    api_objects = []
    if section == "Movies":
        for r in results:
            a = APIObject(r)
            api_objects.append(a)
        return set(api_objects)
    elif section == "TV Shows":
        # Show objects don't have a GUID, so grab the first episode and read it from there
        # This is really inefficient, since to query a single episode, the python-plexapi creates a
        # query for all episodes, and then filters down to one
        for r in results:
            episode = next(iter(r.episodes() or []), None)
            a = APIObject(episode)
            api_objects.append(a)
        return set(api_objects)

    else:
        return "Invalid Section"


def printMedia(media, section):
    count = len(media)
    printHeaderLine()
    print(f"They have {count} items in {section}")
    printHeaderLine()
    for m in media:
        print(m.title)
    printHeaderLine()

# sending post request and saving response as response object
 #tvdbId (int) title (string) qualityProfileId (int) titleSlug (string) images (array) seasons (array)
 #{ tvdbId: '248682',
 # title: 'New Girl',
 # qualityProfileId: 5,
 # titleSlug: 'new-girl',
 # seasons:
 #  [ { seasonNumber: '1', monitored: 'false' },
 #    { seasonNumber: '2', monitored: 'false' },
 #    { seasonNumber: '3', monitored: 'false' },
 #    { seasonNumber: '4', monitored: 'true' } ],
 # path: 'c:\\media\\tv\\New Girl',
 # seasonFolder: true,
 # monitored: true }

def createSearchTermFromMedia(media):
    guid = media.guid
    if media.isMovie():
       return str(f"imdb:{guid}")
    elif media.isShow():
       return str(f"tvdb:{guid}")

def sendMediaToThirdParty(media: list):
    for m in media:
        if m.isShow():
            m.fetchMissingData()

settings = getSettings()

username =  input("MyPlex username:") or settings.get('auth', 'myplex_username')
password = getpass.getpass("MyPlex password:") or settings.get('auth', 'myplex_password')

if username and password:
    account = MyPlexAccount(username, password)
else:
    print("Set a username and passsword in the config file")
    exit(1)

getServers(account)

your_server_name =  input("Your server: ") or settings.get('servers', 'yours')
their_server_name = input("Their server: ") or settings.get('servers', 'theirs')

# returns a PlexServer instance
your_server = account.resource(your_server_name).connect()
# returns a PlexServer instance
their_server = account.resource(their_server_name).connect()

sections = settings.get('sections', 'sections').split(",")
for section in sections:
    your_media = getMedia(your_server, section)
    their_media = getMedia(their_server, section)

    their_new_media = their_media - your_media
    your_new_media = your_media - their_media

    printMedia(their_new_media, section)

    wantedMedia = their_new_media

    sendMediaToThirdParty(wantedMedia)
