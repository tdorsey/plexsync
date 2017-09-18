import configparser
import enum
import requests
from addoptions import *
from base import *
from pick import pick
from setting import *

settings = getSettings()

class ThirdPartyService(enum.Enum):
    Show = "sonarr"
    Movie = "radarr"

class ThirdParty():
    def __init__(self, service):
        self.service = service
        self.qualityProfiles = None #Set quality profiles so the real getter can cache them
        self.addOptions = AddOptions(self.service)
        try:
            self.host = settings.get(service.value, 'host')
            self.apiRoot = "api"
            self.endpointBase = f"{self.host}/{self.apiRoot}/"
            self.endpoints = {"lookup": None, "profile" : "profile", "rootfolder" : "rootfolder" }
            self.apiKey = settings.get(service.value, 'api-key')
            self.headers = {'X-Api-Key': self.apiKey}
            self.rootFolder = self._getRootfolder()

            try:
                self.qualityProfile = settings.get(service.value, 'quality_profile')
            except configparser.NoOptionError:
                self.qualityProfile = self.setQualityProfileSetting()
            if self.service == ThirdPartyService.Show:
                self.endpoints["lookup"] = "series/lookup"
                self.endpoints["add"] = "series"
            elif self.service == ThirdPartyService.Movie:
                self.endpoints["lookup"] = "movies/lookup"
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
            print(f"Request failed: {response.status_code}\n{response.content}")
            return None
        
             
    def createEntry(self, media):
        print(self.qualityProfile)
        if media.type == APIObjectType.Show:
            payload = { 'tvdbId' : media.guid,
                        'title' : media.title,
                        'qualityProfileId' : self.qualityProfile,
                        'titleSlug' : media.titleSlug,
                        'seasons': media.seasons,
                        'images': media.images,
                        'rootFolderPath' : self.rootFolder   
                      }
        elif media.type == APIObjectType.Movie:
            payload = { 'tmdbId' : media.tmdbId,
                        'title' : media.title,
                        'qualityProfileId' : self.qualityProfile,
                        'titleSlug' : media.titleSlug,
                        'images': media.images,
                        'rootFolderPath' : self.rootFolder   
                      }
        
        else:
            print(f"Invalid media type {media} {media.type}")
            return None
    
        try:
            response = requests.post(url = self._buildURL(self.endpoints["add"]), json = payload, headers = self.headers)
            if response.status_code != requests.codes.ok:
                if response.json():
                    print(response.json())
                    return response.json()
                response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
            return None
        print(f"URL: {response.url}")
        print(f"content: {response.content}")

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
        [item] = response.json()
        return item["path"]
