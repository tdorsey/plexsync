import re
import requests
import urllib

from plexapi.video import Video
from base import * 
from thirdparty import ThirdParty
from thirdparty import ThirdPartyService

show_provider = ThirdParty(ThirdPartyService.Show.value)
movie_provider = ThirdParty(ThirdPartyService.Movie.value)

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
       # self.qualityProfileId
       # self.titleSlug
        self.images = []
        self.seasons = []

    def isMovie(self):
        return self.type == APIObjectType.Movie

    def isShow(self):
        return self.type == APIObjectType.Show

    def _createSearchTerm(self):
        if self.isMovie():
          return str(f"imdb:{self.guid}")
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
    
    def fetchMissingData(self):
        lookup_json = self.provider.lookupMedia(self)
        #The media lookup returns an array of results, but we only need the first since we are explicitly 
        #querying the id
        first_item = next((x for x in lookup_json), None)
        self._setMissingData(first_item)

    def _setMissingData(self, data):
       print(f"data is: {data}")
       self.titleSlug = data["titleSlug"]
       self.images = data["images"]
       self.seasons = data["seasons"]
       print(self)

    def _extractGUID(self,guid):
        if not guid:
            return
        match = re.search(r'\d+', guid)
        if match:
            return int(match.group())
