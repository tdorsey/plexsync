#!/usr/bin/python3

from plexapi.myplex import MyPlexAccount
from plexapi.video import Episode, Movie, Show, Video
from pprint import pprint
from pathlib import Path
import os
import configparser
import inspect
import re

class APIObject(Video):
    def __init__(self, video):

      if video.type =="episode":
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
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def getMedia(server, section):
 results = server.library.section(section).search()
 l_title = []
 if section == "Movies":
  for r in results:
   a = APIObject(r)
   l_title.append(a)
  return set(l_title)
 elif section == "TV Shows":
#Show objects don't have a GUID, so grab the first episode and read it from there
#This is really inefficient, since to query a single episode, the python-plexapi creates a 
#query for all episodes, and then filters down to one
  for r in results:
   episode = r.episodes()[0]
   a = APIObject(episode)
   print(a)
   l_title.append(a)
  return set(l_title)

 else: return "Invalid Section"
 
def printMedia(media, section):
 print('*******************')
 print('\n')
 print(str(len(media)) + section + '  they have')
 print('\n')
 for m in media:
  pprint(m.title)
 print('\n')
 print('*******************')

settings = configparser.ConfigParser()
CONFIG_PATH = str(os.path.join(Path.home(),'.config', 'plexsync','config.ini'))
print(f"Reading configuration from {CONFIG_PATH} ")
settings.read(CONFIG_PATH)

account = MyPlexAccount()
getServers(account)

your_server_name = input("Your server: ") or settings.get('Servers', 'yours')
their_server_name = input("Their server: ") or settings.get('Servers', 'theirs')

your_server = account.resource(your_server_name).connect()  # returns a PlexServer instance
their_server = account.resource(their_server_name).connect()  # returns a PlexServer instance

sections = settings.get('sections', 'sections').split(",")
for section in sections:
 your_media = getMedia(your_server, section)
 their_media = getMedia(their_server, section)

 their_new_media = their_media - your_media
 your_new_media = your_media - their_media

 printMedia(their_new_media, section)

