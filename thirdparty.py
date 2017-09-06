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
          self.apiKey = settings.get(service, 'api-key')
          self.host = settings.get(service, 'host')
          self.headers = {'X-Api-Key': self.apiKey}
          self.quality_profiles = self._getQualityProfiles()
          self.root_folder = self._getRootfolder()  
          self.api_root = "api" 
          self.endpoints = dict()
          self.endpoint_base = f"{self.host}/{api_root}/"
          self.endpoints = dict({"lookup": None, "profile" : "profile", "rootfolder" : "rootfolder" })    
          if self.service == ThirdPartyService.Show.value:
                self.endpoints["lookup"] = "series/lookup"
          elif self.service == ThirdPartyService.Movie.value:
                self.endpoints["lookup"] = "movies/lookup"
          else:
            print(f"Unable to set lookup_url for {self.service}") 

        except:
          print(f"Add your {service} api key to the config file")

    def _buildURL(endpoint):
        return str(f"{self.endpoint_base}{endpoint}") 

    def lookupMedia(self, media):
       print("thirdparty is ")
       dump(self)   
       param = {'term' : media.search_term}
       response = requests.get(url = self._buildURL(self.endpoints["lookup"], params = param, headers = self.headers))
       print(f"Searching for: {media.title} - with {media.search_term}")
       return response.json()
    
    def _getQualityProfiles(self):
         response = requests.get(url = self._buildURL(self.endpoints["profile"], headers = self.headers))    
         return response.json()
    
    def _getRootfolder(self):
         response = requests.get(url = self._buildURL(self.endpoints["rootfolder"], headers = self.headers))    
         return response.json()
        
