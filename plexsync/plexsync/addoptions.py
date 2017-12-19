import configparser
import enum

from distutils.util import strtobool

from plexsync.base import *
from plexsync.setting import *
from plexsync.thirdparty import *
from plexsync.thirdpartyservice import *

settings = getSettings()

#ignoreWithFiles: Unmonitors any episodes with a file
#ignoreWithoutFiles: Unmonitors any episodes without a file
#searchForMissing: Searches for missing files after applying ignoreWithFiles and ignoreWithoutFiles
#searchForMovie: Radarr specific

class AddOptions():
    def __init__(self, service):
            self.service = service
            try:
                self.ignoreWithFiles = settings.getboolean(service.value, 'ignore_with_files')
            except configparser.NoOptionError:
                promptString = str(f"Should {service.value} ignore items with files?")
                theSetting = Setting("ignore_with_files", service.value, promptString)
                self.ignoreWithFiles = theSetting.write() 
            try:
                self.ignoreWithoutFiles = settings.getboolean(service.value, 'ignore_without_files')
            except configparser.NoOptionError:
                promptString = str(f"Should {service.value} ignore items without files?")
                theSetting = Setting("ignore_without_files", service.value, promptString)
                self.ignoreWithFiles = theSetting.write() 

            try:
                if self.service == ThirdPartyService.Show:
                    self.searchForMissingEpisodes = settings.getboolean(service.value, 'search_for_missing')
                elif self.service == ThirdPartyService.Movie:
                    self.searchForMovie = settings.getboolean(service.value, 'search_for_missing')
            except configparser.NoOptionError:
                promptString = str(f"Should {service.value} automatically search when items are added?")
                theSetting = Setting("search_for_missing", service.value, promptString)
                self.ignoreWithFiles = theSetting.write() 



