#!/usr/bin/python3

from plexapi.myplex import MyPlexAccount

import re
import enum
import requests
import urllib

from apiobject import APIObject
from base import *
from thirdparty import ThirdParty
from thirdparty import ThirdPartyService

class PlexSync:
    
    def __init__(self):

        self.show_provider = ThirdParty(ThirdPartyService.Show)
        self.movie_provider = ThirdParty(ThirdPartyService.Movie)

        self.account = None
        self.servers = None

    def printHeaderLine():
        print('*******************')

    def getServers(self, account):
        if not account:
            account = self.account
        resources = account.resources()
        self.servers = filter(lambda x: x.provides == 'server', account.resources())
        return self.servers
        for s in servers:
            print(s.name)

    def getAccount(self,username, password):
        if not self.account:
            self.account = MyPlexAccount(username, password)
        return self.account

    def getMedia(self, server, section):
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


    
