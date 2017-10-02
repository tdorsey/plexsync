#!/usr/bin/python3


import re
import enum
import requests
import urllib

from plexapi.myplex import MyPlexAccount

from plexsync.base import *
from plexsync.apiobject import APIObject
from plexsync.thirdparty import ThirdParty, ThirdPartyService

class PlexSync:
    
    def __init__(self):

        self.show_provider = ThirdParty(ThirdPartyService.Show)
        self.movie_provider = ThirdParty(ThirdPartyService.Movie)

        self.account = None
        self.servers = None
    
        self.settings = getSettings()

    def printHeaderLine():
        print('*******************')
    
    def getSettings(self):
        return self.settings

    def getServers(self, account):
        if not account:
            account = self.account
        resources = account.resources()
        self.servers = filter(lambda x: x.provides == 'server', resources)
        return self.servers

    def getServer(self, serverName):
        return self.account.resource(serverName).connect()

    def getAccount(self,username, password):
        if not self.account:
            self.account = MyPlexAccount(username, password)
        return self.account

    def getSections(self, server):
        return server.library.sections()

    def getSection(self, server, section):
        return filter(lambda x: x.name == section, server.library.sections())

    def getResults(self, server, section):
        # guid does not exist in the xml response to it will reload once for each show.
        return server.library.section(section).all()    

    def getMedia(self, server, section):

        results = getResults(server, section)

        api_objects = []
        for r in results:
            a = APIObject(r)
            api_objects.append(a)
        return set(api_objects)

        def printMedia(media, section):
            count = len(media)
            printHeaderLine()
            print(f"They have {count} items in {section}")
            printHeaderLine()
            for m in media:
                print(m.title)
            printHeaderLine()

        def createSearchTermFromMedia(media):
            guid = media.guid
            if media.isMovie():
               return str(f"imdb:{guid}")
            elif media.isShow():
                 return str(f"tvdb:{guid}")

    def sendMediaToThirdParty(self, media: list):
        for m in media:
            m.fetchMissingData()
            m.provider.createEntry(m)

    def compareLibraries(self, yourResults, theirResults):
        yourSet = set()
        theirSet = set()
     
        for r in yourResults:
            yourSet.add(APIObject(r))

        for r in theirResults:
            theirSet.add(APIObject(r))

        return theirSet - yourSet

