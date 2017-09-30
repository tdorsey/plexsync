import re
import requests
import time
import urllib

from plexapi.video import Video

from base import *
from thirdparty import ThirdParty, ThirdPartyService

show_provider = ThirdParty(ThirdPartyService.Show)
movie_provider = ThirdParty(ThirdPartyService.Movie)

class APIObject(Video):
    def __init__(self, video):

        if video.type == "episode":
            self.title = video.show().title
            self.type = APIObjectType.Show
            self.provider = show_provider
        else:
            self.title = video.title
            self.type = APIObjectType.Movie
            self.provider = movie_provider

        self.guid = self._extractGUID(video.guid)
        self.search_term = self._createSearchTerm()
        self.qualityProfileId = None
        self.titleSlug = None
        self.images = []
        self.seasons = []

    def isMovie(self):
        return self.type == APIObjectType.Movie

    def isShow(self):
        return self.type == APIObjectType.Show

    def _createSearchTerm(self):
        if self.isMovie():
            return str(f"imdb:tt{self.guid}")
        elif self.isShow():
            return str(f"tvdb:{self.guid}")

    def __key(self):
        return (self.guid)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(f"GUID is: {self.guid} \n Title is: {self.title}")
        
    def addToLibrary(self):
        add_json = self.provider.createEntry(self)

    def fetchMissingData(self):
        lookup_json = self.provider.lookupMedia(self)
        if lookup_json:
            self._setMissingData(lookup_json)
        
    def _setMissingData(self, data):
        #The media lookup returns a list of results, but we only need the first since we are explicitly
        #querying the id
        print(f"{data} media data")
        [item] = data        

        if self.isMovie():
            self.titleSlug = item["titleSlug"]
            self.images = item["images"]
            self.qualityProfile = item["qualityProfileId"]
            self.year = item["year"]    
            self.tmdbId = item["tmdbId"]    
        elif self.isShow():
            self.titleSlug = item["titleSlug"]
            self.images = item["images"]
            self.seasons = item["seasons"]
            self.qualityProfile = item["qualityProfileId"]
        else:
            print(f"Don't know how to set data for {self.title} - {self.type}") 

    def _extractGUID(self,guid):
        if not guid:
            return
        match = re.search(r'\d+', guid)
        if match:
        #Force padding imdb ids or else anything with leading zeroes fails
            padded = str(match.group().zfill(7))
            return padded

