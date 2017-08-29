#!/usr/bin/python3

import os
import configparser
import getpass
import re

from pathlib import Path

from plexapi.myplex import MyPlexAccount
from plexapi.video import Video

class APIObject(Video):
    def __init__(self, video):

        if video.type == "episode":
            self.title = video.show().title
        else:
            self.title = video.title
        self.type
        self.guid = extractGUID(video.guid)
        self.qualityProfileId
        self.titleSlug
        self.images = []
        self.seasons = []

    def __key(self):
        return (self.guid)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(f"GUID is: {self.guid} \n Title is: {self.title}")

def printHeaderLine():
    print('*******************')

def extractGUID(guid):
    if not guid:
        return
    match = re.search(r'\d+', guid)
    if match:
        return int(match.group())


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

def getSonarrAPIKey():
     return settings.get('api-keys', 'sonarr') or print("Add your sonarr api key to the config file")

def getRadarrAPIKey():
    return settings.get('api-keys', 'radarr') or print("Add your radarr api key to the config file")

settings = configparser.ConfigParser()
CONFIG_PATH = str(os.path.join(
    Path.home(), '.config', 'plexsync', 'config.ini'))
print(f"Reading configuration from {CONFIG_PATH} ")
settings.read(CONFIG_PATH)

username = input("MyPlex username:")
password = getpass.getpass("MyPlex password:")

if username and password:
    account = MyPlexAccount(username, password)
else:
    account = MyPlexAccount()

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
