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
from celery.result import AsyncResult, GroupResult
from plexapi import utils
from plexapi.myplex import MyPlexAccount
from plexsync.apiobject import APIObject, APIObjectType
from plexsync.base import Base
from plexsync.thirdparty import ThirdParty, ThirdPartyService
from distutils.util import strtobool
from .celery import celery, getCelery
from celery.utils.log import get_task_logger
from celery import group, chord

celery_log = get_task_logger(__name__)
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

    @staticmethod
    def getTask(taskID):
        with open('/app/tasktype.txt', 'a') as file:
            task = celery.GroupResult(taskID)
            group_result = PlexSync.getGroupProgress(taskID)
            for k, v in group_result.items():
                file.write(f"Key:{k} - Value:{v}")
            file.write("\n")
            return group_result

    @staticmethod
    def getGroupProgress(taskID):
        task_group = celery.GroupResult.restore(taskID)
        with open("/app/info.txt", "w") as file:

            file.write(f"{task_group}\n\n")

            group_total = 0
            group_current = 0
            for t in task_group.results:
#                file.write(f"Task ID: {t.id} - task state: {t.state}\n\n")
#                file.write(f"task info: {t.info}\n\n")
                status = str(t.info) or t.state

                if t.state in ["FAILURE", "PENDING"]:
                    meta = {'current': 0, 'status': status, 'total': 1}
                    continue
                else:
                    task_current = t.info.get('current', 0)
                    task_total = t.info.get('total', 1)

                    group_current += task_current
                    group_total += task_total
                    file.write(f"@@@{group_current}@@@\n***{group_total}***\n")
        
                    meta = {'current': group_current,
                            'status': 'PROGRESS',
                            'total': group_total}
                    file.write(f'{t.id}-{t.state.upper()}: {meta["current"]} of {meta["total"]}: {int(meta["current"] / meta["total"])}\n')
            return meta

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

    def error_handler(self, uuid):
        result = AsyncResult(uuid)
        ex = result.get(propagate=False)
        logging.exception(
            f"Task {uuid} raised exception: {ex}\n{result.traceback}")

    #@celery.after_setup_logger.connect()
    # def logger_setup_handler(logger, **kwargs ):
     #   my_handler = logging.StreamHandler(sys.stdout)
      #  my_handler.setLevel(logging.DEBUG)
      #  my_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') #custom formatter
       # my_handler.setFormatter(my_formatter)
       # logger.addHandler(my_handler)
       # logging.debug("Celery is logging")

    @celery.task(bind=True)
    def download_media(self, media_info):
        with open("/app/transfer.txt", "w") as file:
            file.write("hi bob")
            file.write(str(self))
            file.write(str(media_info))
            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                file.write(f"Key: {k} - Value: {v}\n")
            server = plexsync.getServer(serverName)
            file.write(f"{str(server)}\n")
            file.write(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))

            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                file.write(f"{len(results)}")
            media = next(iter(results), None)
            file.write(f"{len(results)} Results found\n")
            file.write(f"sectionkey = {section.key} {section.type}\n")
            file.write(f"{media} Media\n")

            plexsync = PlexSync()
            guid = media_info.get("guid")
            serverName = media_info.get("server")
            sectionID = media_info.get("section")
            season = media_info.get("season")
            episode = media_info.get("episode")
            key =  media_info.get("key")
            ratingKey = media_info.get("ratingKey")
            for k,v in media_info.items():
                file.write(f"Key: {k} - Value: {v}\n")
            server = plexsync.getServer(serverName)
            file.write(f"{str(server)}\n")
            file.write(f"{sectionID}")

            section = server.library.sectionByID(str(sectionID))
            
            if section.type == "show":
                results = section.searchEpisodes(guid=guid).pop()
            elif section.type == "movie":
                results = [section.search(guid=guid).pop()]
                file.write(f"{len(results)}")
            media = next(iter(results), None)

            file.write(f"{len(results)} Results found\n")
            file.write(f"sectionkey = {section.key} {section.type}\n")
            file.write(f"{media} Media\n")

            for part in media.iterParts():
                url = media._server.url(
                    f"{part.key}?download=1", includeToken=True)

                token = media._server._token
                headers = {'X-Plex-Token': token}

                response = media._server._session.get(
                    url, headers=headers, stream=True)
                total = int(response.headers.get('content-length', 0))

                chunksize = 4096
                chunks = math.ceil(total / chunksize)
                currentChunk = 0

                with open(media_info["destination"], 'wb') as handle:
                    start = time.time()
                    status = {      "current": 0,
                                    "total": total,
                                    "start": start,
                                    "status": "starting"
                                }
                   # iterationElapsed = time.time() - status_info["start"]
                   # bytesPerSecond = math.floor(chunksize / iterationElapsed)
                   # etaSeconds = math.floor(int(status_info["bytes"]) / bytesPerSecond)
                    #status = {  "bytesPerSecond": bytesPerSecond,
                    #            "iterationElapsed": iterationElapsed,
                    #            "iterationStartTime": status_info["start"],
                    #            "etaSeconds": etaSeconds
                    #        }
                    meta = {'current': 0,
                            'status': "getting started",
                            'total': 1}

                    self.update_state(state='STARTING', meta=meta)

                    for chunk in response.iter_content(chunk_size=chunksize):
                        handle.write(chunk)
                                #iterationElapsed = time.time() - start
                                #bytesPerSecond = math.floor(chunksize / iterationElapsed)
                                #etaSeconds = math.floor(int(status_info["bytes"]) / bytesPerSecond)
                                #currentByte = currentChunk * chunksize
                                #status = {  "bytesPerSecond": bytesPerSecond,
                                #            "iterationElapsed": iterationElapsed,
                                #            "iterationStartTime": status_info["start"],
                                #            "etaSeconds": etaSeconds
                                #          }
                        meta = {        'current': currentChunk,
                                        'status': f"{round(currentChunk / total)}%",
                                        'total': chunks }

                        self.update_state(state='DOWNLOAD', meta=meta)
                        currentChunk += 1
                    totalTimeMS = time.time() - start
                    status = f'{media_info["title"]} Downloaded'
                    meta = {    'current': currentChunk,
                                        'status': status,
                                        'total': chunks,
                                        'totalTimeMS' : totalTimeMS
                           }
                    self.update_state(state='SUCCESS', meta=meta)

                    return meta

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
        if media.type == "episode":
            filename = f"{media.show().title} - {media.seasonEpisode} - {media.title}.{media.media.pop().container}"
        if media.type == "movie":
            filename = f"{media.title} [{media.year}].{media.media.pop().container}"
        self.log.debug(f"{filename}")
        return filename

    def transfer(self, serverName, sectionID, guid):
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
                                media_info["destination"] = os.path.join(
                                    media_info["folderPath"], media_info["fileName"])
                                self.log.debug(f"result: {media_info}, {media}")
                                task = self.download_media.signature(args=[media_info])
                                self.log.debug(f"Task: {task}")
                                episode_list.append(task)

                        job = group(episode_list)
                        group_result = job.delay()
                        group_result.save()
                        self.log.warn(f"grpres: {group_result}")

                        response = {
                        'key': media.key,
                        'guid': media.guid,
                        'title': media.title,
                        'task': group_result.id,
                        'episodes': len(media.episodes()),
                        'seasons': len(media.seasons()) 
                                }
                        media_list.append(response)

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
                            media_info["destination"] = os.path.join(
                                media_info["folderPath"], media_info["fileName"])
                            self.log.warn(f"MediaINF: {media_info}")
                            task = self.download_media.signature(args=[media_info])
                            movie_list = []
                            movie_list.append(task)
                            job = group(movie_list)
                            group_result = job.delay()
                            group_result.save()
                            
                            response = {'key': part.key,
                                        'guid': media.guid,
                                        'title': media.title,
                                        'task': group_result.id}
                                        'section': media.librarySectionID,
                                        'title': media.title,
                                        'folderPath': str(plexsync.createPathForMedia(media)),
                                        'fileName': plexsync.createFilenameForMedia(media)
                                        }
                            media_info["destination"] = os.path.join(
                                media_info["folderPath"], media_info["fileName"])
                            self.log.warn(f"MediaINF: {media_info}")
                            task = self.download_media.signature(args=[media_info])
                            movie_list = []
                            movie_list.append(task)
                            job = group(movie_list)
                            group_result = job.delay()
                            group_result.save()
                            
                            response = {'key': part.key,
                                        'guid': media.guid,
                                        'title': media.title,
                                        'task': group_result.id}
                            media_list.append(response)

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

