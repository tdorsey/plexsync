#!/usr/bin/python3

import enum
import json
import logging
import math
import os
import re
import requests
import urllib
import time

from celery.result import AsyncResult
from plexapi import utils
from plexapi.myplex import MyPlexAccount
from plexsync.apiobject import APIObject, APIObjectType
from plexsync.base import Base
from plexsync.thirdparty import ThirdParty, ThirdPartyService
from distutils.util import strtobool
from tqdm import tqdm
from .celery import celery, getCelery


class PlexSync(Base):

    def __init__(self, taskOnly=False):
        super().__init__()
         
        if taskOnly:
            return

        show_enabled = strtobool(self.settings.get(ThirdPartyService.Show.value, "enabled"))
        movie_enabled = strtobool(self.settings.get(ThirdPartyService.Movie.value, "enabled"))

        if show_enabled:
            self.show_provider = ThirdParty(ThirdPartyService.Show)
        else:
            self.log.info(f"{ThirdPartyService.Show} disabled")
        if movie_enabled:
            self.movie_provider = ThirdParty(ThirdPartyService.Movie)
        else:
            self.log.info(f"{ThirdPartyService.Movie} disabled")
        self.account = self.getAccount()
        self.log.info(f"Account Init: {self.account}")
        self.servers = None

    def printHeaderLine():
        print('*******************')

    def getTask(self, taskID):
        return celery.AsyncResult(taskID)

    def getServers(self, account=None):
        self.log.info(account)
        if account is None:
          account = self.getAccount()
        resources = account.resources()
        self.servers = filter(lambda x: x.provides == 'server', resources)
        return self.servers

    def getOwnedServers(self):
        if not self.servers:
            self.servers = self.getServers()
        ownResources  = filter(lambda x: x.owned == True, self.servers)
        self.log.debug(f"ownResources {ownResources}")
        ownServers = []
        for resource in ownResources:
            ownServers.append(resource.connect())
        self.log.debug(f"ownServers {ownServers}")
        return ownServers

    def getServer(self, serverName):
        return self.account.resource(serverName).connect()

    def getSections(self, server):
        return server.library.sections()

    def getSection(self, server, section):
        return filter(lambda x: x.name == section, server.library.sections())
    
    def getResult(self, sectionID, guid):
         section = self.server.library.sectionByID(sectionID)
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

    def getAPIObject(self, r):
        m = APIObject(r)
        m.fetchMissingData()
        return m

    @celery.task(bind=True,throw=True)
    def transfer(self, server, guid):
        plexsync = PlexSync()
        plexsync.log = logging.getLogger('plexsync')
        plexsync.log.info(f"server - {server}")
        guid = urllib.parse.unquote(guid)
        plexsync.log.info(f"GUID:{guid}")
        server = plexsync.getServer(server)
        for section in server.library.sections():
            plexsync.log.info(f"section title: {section.title}")
            plexsync.log.info(f"{guid}")
            plexsync.log.info(f"{section}")
            results = section.search(guid=guid)
            media = next(iter(results), None)
            if media is None:
              plexsync.log.info(f"{guid} not found in {server.friendlyName} - {section.title}")
              continue
            plexsync.log.info(f"media type - {media.type}")
            if media.type == "show":
               plexsync.log.debug(f"Getting episodes")
               tv_root = plexsync.settings.get('download', 'tv_folder')
               show_folder_path = os.path.join(tv_root, f"{media.title}")
               plexsync.create_dir(show_folder_path)
               for season in media.seasons():
                  season_folder_path = os.path.join(show_folder_path, f"Season {season.seasonNumber}")
                  plexsync.create_dir(season_folder_path)
                  plexsync.log.info(f"Starting Season {season.seasonNumber} - {len(season.episodes())} Episodes")
                  for episode in season:
                      plexsync.log.info(f"Starting {episode.title}")
                      tmp = episode.download(season_folder_path)
                      episode_path =  str(f"{episode.show().title} - {episode.seasonEpisode} - {episode.title}.{episode.media[0].container}") 
                      dest = os.path.join(season_folder_path, episode_path)
                      os.rename(tmp[0], dest)
            if media.type == "movie":
                for part in media.iterParts():
                # We do this manually since we dont want to add a progress to Episode etc
                 renamed_file = f"{media.title} [{media.year}].{part.container}"
                 savepath = plexsync.settings.get('download', 'movies_folder')
                 plexsync.log.debug(f"savepath: {savepath}")
                 plexsync.log.debug(f"media: {media}")
                 plexsync.log.debug(f"server: {media._server}")
                 plexsync.log.debug(f"{media._server._baseurl} {part.key} {media._server._token}")
                 url = media._server.url(f"{part.key}?download=1", includeToken=True)
                 plexsync.log.debug(f"url: {url}")
                 renamed_file = f"{media.title} [{media.year}].{part.container}"
                 plexsync.log.debug(renamed_file)
                 
                 token = media._server._token
                 headers = {'X-Plex-Token': token}

                response = media._server._session.get(url, headers=headers, stream=True)
                total = int(response.headers.get('content-length', 0))
                chunksize = 4096
                chunks = math.ceil( total / chunksize )
                currentChunk = 0
                fullpath = os.path.join(savepath, renamed_file)
                plexsync.log.debug(f"{fullpath}")
                plexsync.log.debug(f"total: {total}")
                STATUS_CHUNK_INCREMENT = 10000
                nextStatusChunk = STATUS_CHUNK_INCREMENT

                with open(fullpath, 'wb') as handle:
                    for chunk in response.iter_content(chunk_size=chunksize):
                            chunkMessage = f"Chunk {currentChunk} of {chunks}"

                            iterationStartTime = time.time()
                            currentChunk += 1
                            handle.write(chunk)
                            if ( currentChunk > nextStatusChunk ): #Approx every 40 MB
                                iterationElapsed = time.time() - iterationStartTime
                                iterationBytes = chunksize * currentChunk
                                bytesPerSecond = iterationBytes / iterationElapsed
                                etaSeconds = math.floor( total / bytesPerSecond )
                                status = {"chunkMessage" : chunkMessage,
                                          "currentChunk" : currentChunk,
                                          "totalChunks" : chunks,
                                          "chunkSize" : chunksize,
                                          "totalBytes" : total,
                                          "bytesPerSecond": bytesPerSecond,
                                          "iterationElapsed": iterationElapsed,
                                          "iterationBytes": iterationBytes,
                                          "iterationStartTime": iterationStartTime,
                                          "etaSeconds": etaSeconds
                                        }
                                nextStatusChunk = nextStatusChunk + STATUS_CHUNK_INCREMENT

                            else:
                                status = { "currentChunk" : currentChunk,"STATUS_CHUNK_INCREMENT" : STATUS_CHUNK_INCREMENT,  "nextStatusChunk" : nextStatusChunk, "chunkMessage" : chunkMessage, "condition" : currentChunk > nextStatusChunk}

                            meta = {'current': currentChunk, 
                                    'status': status,
                                    'total': chunks }
                                
                            self.update_state(state='PROGRESS', meta=meta)

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
