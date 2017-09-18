import configparser
import enum
from base import *
from setting import *
from distutils.util import strtobool
settings = getSettings()

#ignoreWithFiles: Unmonitors any episodes with a file
#ignoreWithoutFiles: Unmonitors any episodes without a file
#searchForMissing: Searches for missing files after applying ignoreWithFiles and ignoreWithoutFiles

class AddOptions():
    def __init__(self, service):
            self.service = service
            try:
                self.ignoreWithFiles = settings.getboolean(service.value, 'ignore_with_files')
            except configparser.NoOptionError:
                theSetting = Setting("ignore_with_files", str(f"Should {service.value} ignore items with files?"))
                self.ignoreWithFiles = self.setSetting(theSetting) 
            try:
                self.ignoreWithoutFiles = settings.getboolean(service.value, 'ignore_without_files')
            except configparser.NoOptionError:
                theSetting = Setting("ignore_without_files", str(f"Should {service.value} ignore items without files?"))
                self.ignoreWithFiles = self.setSetting(theSetting) 
            try:
                self.ignoreWithFiles = settings.getboolean(service.value, 'search_for_missing')
            except configparser.NoOptionError:
                theSetting = Setting("search_for_missing", str(f"Should {service.value} automatically search when added?"))
                self.searchMissing = self.setSetting(theSetting) 

    def setSetting(self, setting):
            _section = self.service.value
            print(f"setting {setting.key} for {_section}")

            user_input = input(setting.prompt)
            setting.value = str(user_input)

            settings.set(_section, setting.key, setting.value)
            writeSettings(settings)
            return setting.value

