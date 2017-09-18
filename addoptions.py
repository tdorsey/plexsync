import configparser
import enum
from base import *
from distutils.util import strtobool
settings = getSettings()

#ignoreEpisodesWithFiles: Unmonitors any episodes with a file
#ignoreEpisodesWithoutFiles: Unmonitors any episodes without a file
#searchForMissingEpisodes: Searches for missing files after applying ignoreEpisodesWithFiles and 
ignoreEpisodesWithoutFiles


class AddOptions():
    def __init__(self, service):
            self.service = service
            try:
                self.ignoreEpisodesWithFiles = settings.get(service.value, 'ignoreWithFiles')
            except configparser.NoOptionError:
                self.ignoreEpisodesWithFiles = self.setIgnoreWithFilesSetting()
            try:
                self.ignoreEpisodesWithoutFiles = settings.get(service.value, 'ignoreWithoutFiles')
            except configparser.NoOptionError:
                self.ignoreEpisodesWithFiles = self.setIgnoreWithoutFilesSetting()
            try:
                self.ignoreEpisodesWithFiles = settings.get(service.value, 'searchForMissing')
            except configparser.NoOptionError:
                self.ignoreEpisodesWithFiles = self.setSearchForMissingSetting()

    def setIgnoreWithFilesSetting(self):
            print("setting ignore with files")
            KEY = 'ignore_with_files'
            section = self.service.value
            ignore_with_files_string = str(strtobool(input("Ignore with files?:")))
            settings.set(section, KEY, ignore_with_files_string)
            writeSettings(settings)
            return ignore_with_files_string

    def setIgnoreWithoutFilesSetting(self):
            print("setting ignore without files")
            KEY = 'ignore_without_files'
            section = self.service.value
            ignore_without_files_string = str(strtobool(input("Ignore without files?:")))
            settings.set(section, KEY, ignore_without_files_string)
            writeSettings(settings)
            return ignore_without_files_string

    def setSearchForMissingSetting(self):
            print("setting search for missing")
            KEY = 'search_for_missing'
            section = self.service.value
            search_for_missing_string = str(strtobool(input("Search for missing files?:")))
            settings.set(section, KEY, search_for_missing_string)
            writeSettings(settings)
            return search_for_missing_string
