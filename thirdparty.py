import enum
import requests
from base import *
settings = getSettings()

class ThirdPartyService(enum.Enum):
    Show = "sonarr"
    Movie = "radarr"

class ThirdParty():
    def __init__(self, service):
        self.service = service
        try:
            self.host = settings.get(service.value, 'host')
            self.api_root = "api"
            self.endpoint_base = f"{self.host}/{self.api_root}/"
            self.endpoints = {"lookup": None, "profile" : "profile", "rootfolder" : "rootfolder" }
            self.apiKey = settings.get(service.value, 'api-key')
            self.headers = {'X-Api-Key': self.apiKey}
            self.quality_profiles = self._getQualityProfiles()
            self.root_folder = self._getRootfolder()

            if self.service == ThirdPartyService.Show:
                self.endpoints["lookup"] = "series/lookup"
                self.endpoints["add"] = "series"
            elif self.service == ThirdPartyService.Movie:
                self.endpoints["lookup"] = "movies/lookup"
                self.endpoints["add"] = "movies"
            else:
                print(f"Unable to set endpoints for {self.service}")

        except Exception as e:
            print(e.message)
            print(f"Add your {service} api key to the config file")

    def _buildURL(self, endpoint):
        return str(f"{self.endpoint_base}{endpoint}")

    def lookupMedia(self, media):
        param = {'term' : media.search_term}
        response = requests.get(url = self._buildURL(self.endpoints["lookup"]), params = param, headers = self.headers)
        print(f"Searching for: {media.title} - with {media.search_term}")
        return response.json()

    def createEntry(self, media):
        payload = { 'tvdbId' : media.guid,
                     'title' : media.title,
                     'qualityProfileId' : media.qualityProfile,
                     'titleSlug' : media.titleSlug,
                     'seasons': media.seasons,
                     'images': media.images}
        response = requests.post(url = self._buildURL(self.endpoints["add"]), data = payload, headers = self.headers)
        print(f"Adding {media.type} {media.title} ")
        return response.json()

    def _getQualityProfiles(self):
        response = requests.get(url = self._buildURL(self.endpoints["profile"]), headers = self.headers)
        quality_list = response.json()
        return response.json()

    def _getRootfolder(self):
        response = requests.get(url = self._buildURL(self.endpoints["rootfolder"]), headers = self.headers)
        [item] = response.json()
        return item["path"]
