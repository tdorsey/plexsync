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
import threading
import pathlib
from plexapi import utils
from plexapi.myplex import MyPlexAccount
from plexsync.apiobject import APIObject, APIObjectType
from plexsync.base import Base
from plexsync.thirdparty import ThirdParty, ThirdPartyService
from distutils.util import strtobool

log = logging.getLogger('plexsync')

class PlexSync(Base):

    def __init__(self):
        super().__init__()

        show_enabled = strtobool(self.settings.get(
            ThirdPartyService.Show.value, "enabled"))
        movie_enabled = strtobool(self.settings.get(
            ThirdPartyService.Movie.value, "enabled"))

        if show_enabled:
            self.show_provider = ThirdParty(ThirdPartyService.Show)
        else:
            self.log.info(f"{ThirdPartyService.Show.value} disabled")
        if movie_enabled:
            self.movie_provider = ThirdParty(ThirdPartyService.Movie)
        else:
            self.log.info(f"{ThirdPartyService.Movie.value} disabled")
        self.account = self.getAccount()
        self.log.info(f"Account Init: {self.account}")
        self.servers = None

    @staticmethod
    def printHeaderLine():
        print('*******************')

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
        ownResources = filter(lambda x: x.owned == True, self.servers)
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
            return server.library.section(section)

    def getResult(self, sectionID, guid):
        section = self.server.library.sectionByID(sectionID)
        result = section.search(guid=guid)
        self.log.debug(guid)
        return result

    def getResults(self, server, section):
        # guid does not exist in the xml response to it will reload once for each show.
        result = server.library.section(section)
        return result.all()

    def getAPIObjects(self, results):
        api_objects = []
        for r in results:
            a = APIObject(r)
            api_objects.append(a)
        return set(api_objects)

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

    def prepareMediaTemplate(self, result):
                m = self.getAPIObject(result)

                result_dict = {}
                result_dict['title'] = m.title
                result_dict['downloadURL'] = m.downloadURL
                result_dict['overview'] = m.overview
                result_dict['sectionID'] = m.librarySectionID
                result_dict['year'] = m.year
                result_dict['guid'] = urllib.parse.quote_plus(m.guid)
                result_dict['server'] = result._server.friendlyName
                if m.image and len(m.image) > 0:
                    result_dict['image'] = m.image
                result_dict['rating'] = m.rating

                return result_dict


    def compareLibraries(self, yourResults, theirResults):
        self.log.debug("Comparing libraries")
        yourSet = set(yourResults)
        theirSet = set(theirResults)

        results = theirSet - yourSet
        resultsList = list(results)
        resultsList.sort(key=lambda x: x.title)
        return resultsList

    def getAPIObject(self, r):
        m = APIObject(r)
        m.fetchMissingData()
        return m

  
    def render(self, message):
      log = logging.getLogger('plexsync')
      log.debug("Plexsync rendering")

    def createPathForMedia(self, media):
        if media.type == "episode":
            tv_root = self.settings.get('download', 'tv_folder')
            show_folder_path = os.path.join(tv_root, f"{media.show().title}")
            season_folder_path = os.path.join(
                show_folder_path, f"Season {media.seasonNumber}")
            path = self.create_dir(season_folder_path)
        if media.type == "movie":
            movie_root = self.settings.get('download', 'movies_folder')
            path = self.create_dir(movie_root)
        return path

    def createFilenameForMedia(self, media):
        import pdb; pdb.set_trace()
        self.log.debug(f"{media}")
        self.log.debug(f"{len(media.media)} length")
        if media.type == "episode":
            filename = f"{media.show().title} - {media.seasonEpisode} - {media.title}.{media.media.pop().container}"
        if media.type == "movie":
            filename = f"{media.title} [{media.year}].{media.media.pop().container}"
        self.log.debug(f"{filename}")

        return filename

    def buildMediaInfo(self, serverName, sectionID, guid):
        try:
                    plexsync = PlexSync()
                    server = plexsync.getServer(serverName)
                    section = server.library.sectionByID(sectionID)
                    self.log.warn(f"sectionkey = {section.key} {section.type}")
                    results = section.search(guid=guid)
                    self.log.warn(f"{section.title} {section.type}")
                    self.log.warn(f"{len(results)} Results found")

                    if len(results) == 1:
                        media = results.pop()
                        self.log.warn(f"{media} Media")

                    else:
                        self.log.warn("too many results")
                    media_list = []
                    
                    if media and media.type == "show":
                        episode_list = [] 
                        for season in media.seasons():
                            for episode in season:
                                media_info = {'guid': episode.guid,
                                            'key': episode.key,
                                            'ratingKey': episode.ratingKey,
                                            'server': server.friendlyName,
                                            'section': media.librarySectionID,
                                            'title': episode.title,
                                            'season': season.title,
                                            'episode': episode.index,
                                            'folderPath': str(plexsync.createPathForMedia(episode)),
                                            'fileName': plexsync.createFilenameForMedia(episode)
                                            }
                                media_info["destination"] = os.path.join(media_info["folderPath"], media_info["fileName"])
                                self.log.debug(f"result: {media_info}, {media}")
                                media_list.append(media_info)

                    if media and media.type == "movie":
                        for part in media.iterParts():
                            media_info = {'guid': media.guid,
                                        'key': part.key,
                                        'server': server.friendlyName,
                                        'section': sectionID,
                                        'title': media.title,
                                        'folderPath': str(plexsync.createPathForMedia(media)),
                                        'fileName': plexsync.createFilenameForMedia(media)
                                        }
                            
                            media_info["destination"] = os.path.join(media_info["folderPath"], media_info["fileName"])
                            self.log.warn(f"MediaINF: {media_info}")
                      
                            media_info["destination"] = os.path.join(media_info["folderPath"], media_info["fileName"])
                            self.log.warn(f"MediaINF: {media_info}")
                            
                            media_list.append(media_info)

                    return media_list
        except Exception as e:
            self.log.exception(e)

    def download(self, media):
        log = logging.getLogger('plexsync')
        try:
            for part in media.iterParts():
                url = media._server.url(
                    f"{part.key}?download=1", includeToken=True)
                self.log.debug(f"url: {url}")
                renamed_file = f"{media.title} [{media.year}].{part.container}"
                log.debug(renamed_file)
                downloaded_file = media.download(savepath=savepath)
                log.debug(f"downloaded {renamed_file}")
        except Exception as e:
            log.debug(e)

