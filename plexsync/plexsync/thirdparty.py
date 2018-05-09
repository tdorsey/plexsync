import configparser
import enum
import json
import requests
import logging

from plexsync.addoptions import *
from plexsync.base import *
from plexsync.setting import *
from plexsync.thirdpartyservice import *


from pick import pick

class ThirdParty(Base):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.qualityProfiles = None #Set quality profiles so the real getter can cache them
        self.addOptions = AddOptions(self.service)
        try:
            self.host = self.settings.get(service.value, 'host')
            self.apiRoot = "api"
            self.endpointBase = f"{self.host}/{self.apiRoot}/"
            self.endpoints = {"lookup": None, "profile" : "profile", "rootfolder" : "rootfolder" }
            self.apiKey = self.settings.get(service.value, 'api-key')
            self.headers = {'X-Api-Key': self.apiKey}
            self.rootFolder = self._getRootfolder()

            try:
                self.qualityProfile = self.settings.get(service.value, 'quality_profile')
            except configparser.NoOptionError:
                self.qualityProfile = self.setQualityProfileSetting()
            if self.service == ThirdPartyService.Show:
                self.endpoints["lookup"] = "series/lookup"
                self.endpoints["add"] = "series"
            elif self.service == ThirdPartyService.Movie:
                self.endpoints["lookup"] = "movie/lookup"
                self.endpoints["add"] = "movie"
            else:
                print(f"Unable to set endpoints for {self.service}")

        except Exception as e:
            print(e.message)

    def _buildURL(self, endpoint):
        return str(f"{self.endpointBase}{endpoint}")
    
    def setQualityProfileSetting(self):
            promptString = str(f"Choose a default quality profile for {self.service.value}")
            setting = Setting("quality_profile", self.service.value, promptString)
            print("getting profiles")        
            profile_list = self._getQualityProfiles()
            option, index = pick([p['name'] for p in profile_list], promptString, min_selection_count=1)
            profile = profile_list[index]
            setting.value = str(profile['id'])
            print(f"Setting is {setting.key} {setting.value}")
            print(f"profile id  is {profile['id']}")
            user_profile_id = setting.write()
            print(f"user id is {user_profile_id}")
            return user_profile_id

    def lookupMedia(self, media):
        param = {'term' : media.search_term}
        response = requests.get(url = self._buildURL(self.endpoints["lookup"]), params = param, headers = self.headers)
        print(f"Searching for: {media.title} - with {media.search_term}")
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            response.raise_for_status()
        
    def _buildPayload(self, media):
        if self.service == ThirdPartyService.Show:
            return  { 
                            'tvdbId' : media.guid,
                            'title' : media.title,
                            'qualityProfileId' : self.qualityProfile,
                            'titleSlug' : media.titleSlug,
                            'seasons': media.seasons,
                            'images': media.images,
                            'year': media.year,
                            'rootFolderPath' : self.rootFolder,
                            'addOptions' :  { 
                                                'ignoreEpisodesWithFiles' : self.addOptions.ignoreWithFiles,
                                                'ignoreEpisodesWithoutFiles' : self.addOptions.ignoreWithoutFiles,
                                                'searchForMissingEpisodes' : self.addOptions.searchForMissingEpisodes
                                            }
                                           
                    }
        elif self.service == ThirdPartyService.Movie:
             return  { 
                            'tmdbId' : media.tmdbId,
                            'title' : media.title,
                            'qualityProfileId' : self.qualityProfile,
                            'titleSlug' : media.titleSlug,
                            'images': media.images,
                            'year': media.year,
                            'rootFolderPath' : self.rootFolder,
                            'addOptions' :  { 
                                                'ignoreEpisodesWithFiles' : self.addOptions.ignoreWithFiles,
                                                'ignoreEpisodesWithoutFiles' : self.addOptions.ignoreWithoutFiles,
                                                'searchForMovie' : self.addOptions.searchForMovie
                                            }
                                           
                    }

             
    def createEntry(self, media):
        payload = self._buildPayload(media)
        print(f"{media.title}")
        print(f"Payload is: {payload}")
        try:
            response = requests.post(url = self._buildURL(self.endpoints["add"]), data = json.dumps(payload), headers = self.headers)
            if response.status_code != requests.codes.ok:
                if response.json():
                    print(f"Response code {response.status_code} response {response.content}")
                    print(response.json())
                    return response.json()
                response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
            return None


        print(f"{response.status_code} \n {response.content}")
        print(f"Adding {media.type} {media.title} ")
        return response.json()

    def _getQualityProfiles(self):
        if not self.qualityProfiles:
            response = requests.get(url = self._buildURL(self.endpoints["profile"]), headers = self.headers)
            self.qualityProfiles = response.json()
        return self.qualityProfiles
    def _getRootfolder(self):
        response = requests.get(url = self._buildURL(self.endpoints["rootfolder"]), headers = self.headers)
        item = response.json()
        self.log.info(item)
        #return item["path"]
