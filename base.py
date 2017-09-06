import configparser
import enum
import os
import sys

from pathlib import Path

class APIObjectType(enum.Enum):
    Show = 1
    Movie = 2
class ThirdPartyService(enum.Enum):
    Show = "sonarr"
    Movie = "radarr"
class ThirdParty():
    def __init__(self, service):
        self.service = service
        try:
          self.apiKey = settings.get(service, 'api-key')
          self.host = settings.get(service, 'host')
          if self.service == ThirdPartyService.Show.value:
                self.lookup_url = str(f"{self.host}/api/series/lookup")
          elif self.service == ThirdPartyService.Movie.value:
                self.lookup_url = str(f"{self.host}/api/movies/lookup")
          else:
            print(f"Unable to set lookup_url for {self.service}") 

        except:
          print(f"Add your {service} api key to the config file")

def getSettings():
        settings = configparser.ConfigParser()
        CONFIG_PATH = str(os.path.join(Path.home(), '.config', 'plexsync', 'config.ini'))
        print(f"Reading configuration from {CONFIG_PATH} ")
        settings.read(CONFIG_PATH)        
        return settings




#Create a module level instance of settings
this = sys.modules[__name__]
this.settings = None
this.settings = getSettings()

