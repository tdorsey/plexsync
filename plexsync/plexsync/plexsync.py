#!/usr/bin/python3

import re
import enum
import requests
import urllib
import logging
import os


from celery import Celery


from plexapi.myplex import MyPlexAccount
from plexapi import utils

from plexsync.base import Base
from plexsync.apiobject import APIObject, APIObjectType
from plexsync.thirdparty import ThirdParty, ThirdPartyService

class PlexSync(Base):
    
    def __init__(self):
        super().__init__()

        self.tasks = Celery('tasks', broker='pyamqp://guest@localhost',backend='redis://localhost')
  
        self.show_provider = ThirdParty(ThirdPartyService.Show)
        self.movie_provider = ThirdParty(ThirdPartyService.Movie)

        self.account = None
        self.servers = None

    def printHeaderLine():
        print('*******************')
    
    def getServers(self, account=None):
        if not account:
            account = self.account
        resources = account.resources()
        self.servers = filter(lambda x: x.provides == 'server', resources)
        return self.servers

    def getOwnedServers(self):
        if not self.servers:
            self.servers = self.getServers()
        ownResources  = filter(lambda x: x.owned == True, self.servers)
        self.log.debug("ownResources {ownResources}")
        ownServers = []
        for resource in ownResources:
            ownServers.append(resource.connect())
        self.log.debug("ownServers {ownServers}")
        return ownServers

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
    
    def getResult(self, sectionID, guid):
         section = self.server.library.section(section)
         result = section.search(guid=guid)
         print(guid)
         return result

    def getResults(self, server, section):
        # guid does not exist in the xml response to it will reload once for each show.
        return server.library.section(section).all()    

    def getMedia(self, server, section):

        results = self.getResults(server, section)

        api_objects = []
        for r in results:
            a = APIObject(r)
            api_objects.append(a)
        return set(api_objects)
   
    def printMedia(self, media, section):
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

    def sendMediaToThirdParty(self, m):
            m.fetchMissingData()
            return m.provider.createEntry(m)

    def sendMediaListToThirdParty(self, media: list):
        for m in media:
            m.fetchMissingData()
            m.provider.createEntry(m)

    def compareLibrariesAsResults(self, yourResults, theirResults):
        yourSet = set()
        theirSet = set()
     
        for r in yourResults:
            yourSet.add(r)

        for r in theirResults:
            theirSet.add(r)

        results = theirSet - yourSet
        resultsList = list(results)
        resultsList.sort(key=lambda x: x.title)
        return resultsList
    def compareLibraries(self, yourResults, theirResults):
        yourSet = set()
        theirSet = set()

        for r in yourResults:
            yourSet.add(APIObject(r))

        for r in theirResults:
            theirSet.add(APIObject(r))

        return theirSet - yourSet

    def getAPIObject(self, r):
        m = APIObject(r)
        m.fetchMissingData()
        return m

    @tasks.task
    def transfer(self, media):

        self.log.debug('transfer')
        try:
            if media.type == "show":
               self.log.debug(f"Getting episodes")
               tv_root = self.settings.get('download', 'tv_folder')
               show_folder_path = os.path.join(tv_root, f"{media.title}")
               self.create_dir(show_folder_path)
               for season in media.seasons():
                  season_folder_path = os.path.join(show_folder_path, f"Season {season.seasonNumber}")
                  self.create_dir(season_folder_path)
                  self.log.info(f"Starting Season {season.seasonNumber} - {len(season.episodes())} Episodes")
                  for episode in season:
                    self.log.info(f"Starting {episode.title}")
                    tmp = episode.download(season_folder_path)
                    episode_path =  str(f"{episode.show().title} - {episode.seasonEpisode} - {episode.title}.{episode.media[0].container}") 
                    dest = os.path.join(season_folder_path, episode_path)
                    os.rename(tmp[0], dest)
            if media.type == APIObjectType.Movie:
               for part in media.iterParts():
                 #We do this manually since we dont want to add a progress to Episode etc
                  renamed_file = f"{media.title} [{media.year}].{part.container}"
                  savepath = self.settings.get('download', 'movie_folder')
                  self.log.debug(f"savepath: {savepath}")
                  self.log.debug(f"media: {media}")
                  self.log.debug(f"server: {media._server}")
                  self.log.debug(f"{media._server._baseurl} {part.key} {media._server._token}")
                  url = media._server.url(f"{part.key}?download=1", includeToken=True)
                  self.log.debug(f"url: {url}")
                  renamed_file = f"{media.title} [{media.year}].{part.container}"
                  self.log.debug(renamed_file)
                  filepath = utils.download(url=url,
                                            filename=renamed_file,
                                            savepath=savepath,
                                            session=media._server._session,
                                            token=media._server._token)
                  self.log.debug(f"{filepath}")
                  self.log.debug(f"downloaded {renamed_file}")
        except Exception as e:
            self.log.debug(e)
    def download(self, media):
        log = logging.getLogger('plexsync')
        try:
            for part in media.iterParts():
                url = media._server.url(f"{part.key}?download=1", includeToken=True)
                self.log.debug(f"url: {url}")
                renamed_file = f"{media.title} [{media.year}].{part.container}"
                log.debug(renamed_file) 
                downloaded_file = media.download(savepath=savepath)
                log.debug(f"downloaded {renamed_file}")
        except Exception as e:
            log.debug(e)

