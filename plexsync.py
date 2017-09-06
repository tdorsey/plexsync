#!/usr/bin/python3

from pathlib import Path

import os
import configparser
import getpass
import re
import enum
import requests
import urllib

from plexapi.myplex import MyPlexAccount
from plexapi.video import Video

class APIObjectType(enum.Enum):
    Show = 1
    Movie = 2
class ThirdPartyService(enum.Enum):
    Show = "sonarr"
    Movie = "radarr"
class ThirdParty():
    def __init__(self, service, host, apiKey):
        self.host = host
        self.apiKey = apiKey
        self.service = service
class APIObject(Video):
    def __init__(self, video):

        if video.type == "episode":
            self.title = video.show().title
            self.type = APIObjectType.Show
        else:
            self.title = video.title
            self.type = APIObjectType.Movie
        
        self.guid = extractGUID(video.guid)
       # self.qualityProfileId
       # self.titleSlug
        self.images = []
        self.seasons = []

    def isMovie(self):
        return self.type == APIObjectType.Movie

    def isShow(self):
        return self.type == APIObjectType.Show

    def __key(self):
        return (self.guid)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(f"GUID is: {self.guid} \n Title is: {self.title}")
    
    def setMissingData(self, queried_data):
       print(f"queried_data is: {queried_data}")
       self.titleSlug = queried_data.titleSlug

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

def getThirdParty(service):
    try:
        apiKey = settings.get(service, 'api-key') 
        host = settings.get(service, 'host')
    except:
        print(f"Add your {service} api key to the config file")
    return ThirdParty(service, host, apiKey) 
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

def lookupMedia(media):
    if media.isShow():
        provider = getThirdParty("sonarr")
        endpoint_url = str(f"{provider.host}/api/series/lookup")
    elif media.isMovie():
        provider = getThirdParty("radarr")
        endpoint_url = str(f"{provider.host}/api/series/lookup") 

    headers = {'X-Api-Key': provider.apiKey}   
    search_term = createSearchTermFromMedia(media)
    param = {'term' : search_term}

    response = requests.get(url = endpoint_url, params = param, headers = headers)
    print(f"Searching for: {media.title} - with {search_term}")        
    return response.json()

def sendMediaToThirdParty(media: list):
    for m in media:
        if m.isMovie():
            provider =  getThirdParty("radarr")
        elif m.isShow():
            provider = getThirdParty("sonarr")
        else:
            print(f"Invalid APIObject Type {m.type}")

#        escaped_title = urllib.parse.quote(m.title)   
        if m.isShow():
            queried_data = lookupMedia(m)
            first_item = next((x for x in queried_data), None)  
            m.setMissingData(first_item)
        

settings = configparser.ConfigParser()
CONFIG_PATH = str(os.path.join(
    Path.home(), '.config', 'plexsync', 'config.ini'))
print(f"Reading configuration from {CONFIG_PATH} ")
settings.read(CONFIG_PATH)

#Set plexauth configuration in our config file
os.environ["PLEXAPI_CONFIG_PATH"] = CONFIG_PATH


username =  input("MyPlex username:") or settings.get('auth', 'myplex_username')
password = getpass.getpass("MyPlex password:") or settings.get('auth', 'myplex_password')

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

    wantedMedia = their_new_media

    sendMediaToThirdParty(wantedMedia)
