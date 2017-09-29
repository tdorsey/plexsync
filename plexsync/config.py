import configparser
import enum
from base import *
from distutils.util import strtobool
settings = getSettings()



class Config():
    def __init__(self, service):
            self.service = service
            try:
                self.ignoreWithFiles = settings.get(service.value, 'ignoreWithFiles')
            except configparser.NoOptionError:
                self.ignoreWithFiles = self.setIgnoreWithFilesSetting()
            try:
                self.ignoreWithoutFiles = settings.get(service.value, 'ignoreWithoutFiles')
            except configparser.NoOptionError:
                self.ignoreWithoutFiles = self.setIgnoreWithoutFilesSetting()
            try:
                self.searchForMissing = settings.get(service.value, 'searchForMissing')
            except configparser.NoOptionError:
                self.searchForMissing = self.setSearchForMissingSetting()

    def setIgnoreWithFilesSetting(self):
            print(f"setting ignore with files for {self.service.value}")
            KEY = 'ignore_with_files'
            section = self.service.value
            ignore_with_files_string = str(strtobool(input("Ignore with files?:")))
            settings.set(section, KEY, ignore_with_files_string)
            writeSettings(settings)
            return ignore_with_files_string

    def setIgnoreWithoutFilesSetting(self):
            print(f"setting ignore without files for {self.service.value}")
            KEY = 'ignore_without_files'
            section = self.service.value
            ignore_without_files_string = str(strtobool(input("Ignore without files?:")))
            settings.set(section, KEY, ignore_without_files_string)
            writeSettings(settings)
            return ignore_without_files_string

    def setSearchForMissingSetting(self):
            print(f"setting search for missing for {self.service.value}")
            KEY = 'search_for_missing'
            section = self.service.value
            search_for_missing_string = str(strtobool(input("Search for missing files?:")))
            settings.set(section, KEY, search_for_missing_string)
            writeSettings(settings)
            return search_for_missing_string
