import enum
import logging
import re
import requests
import time
import traceback
import urllib

from pprint import pprint
from plexapi.video import Video
def _hash(self):
    return hash(self.title) 

def _eq(self, other):
    return (self.title == other.title)

Video.__hash__ = _hash
Video.__eq__ = _eq

from plexsync.base import Base
from plexsync.thirdparty import ThirdParty, ThirdPartyService

class APIObjectType(enum.Enum):
    Show = "show"
    Movie = "movie"
    Episode = "episode"


class APIObject(Base):
    def __init__(self, video):
      try:
        super().__init__()
        self.guid = video.guid
        self.type = video.type
        self.overview = video.summary
        self.rating = video.rating
        self.year = video.year
        self.title = video.title
        self.guid = video.guid
        self.image = video.artUrl
        self.qualityProfileId = None
        self.titleSlug = None
        self.librarySectionID = video.librarySectionID
        self.downloadURL = self._getDownloadURL(video)
        self.provider = None

        if video.type == "show":
          if self.settings.get(ThirdPartyService.Show.value, "enabled") is True:
             self.provider = ThirdParty(ThirdPartyService.Show)
         
          self.seasons = []
          self.title = video.title
          self.type = APIObjectType.Show

        elif video.type == "episode":
            if self.settings.get(ThirdPartyService.Show.value, "enabled") is True:
              self.provider = ThirdParty(ThirdPartyService.Show)

            self.guid = video.show().guid
            self.title = video.title
            self.type = APIObjectType.Show

        elif video.type == "movie":
           self.type = APIObjectType.Movie
           if self.settings.get(ThirdPartyService.Movie.value, "enabled") is True:
              self.provider = ThirdParty(ThirdPartyService.Movie)
        else:
            self.log.debug(f"Unable to determine Object Type for {video}")
            return None

        if self.provider:
            self.search_term = self._createSearchTerm()

      except:
        traceback.print_exc()

    def _createSearchTerm(self):
        shortGUID = self._extractGUID(self.guid)
        if self.type == APIObjectType.Movie.value:
            return str(f"imdb:tt{shortGUID}")
        elif self.type == APIObjectType.Show.value:
            return str(f"tvdb:{shortGUID}")

    def _getDownloadURL(self, video):
        if self.type == APIObjectType.Movie.value:
             for part in video.iterParts():
                 url = video._server.url(f"{part.key}?download=1", includeToken=True)
             return url
        elif self.type == APIObjectType.Show.value:
             episode =  video.episodes()[0]
             for part in episode.iterParts():
                 url = episode._server.url(f"{part.key}?download=1", includeToken=True)
             return url

    def __key(self):
        return (self.guid)

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        return str(f"GUID is: {self.guid} \n Title is: {self.title}")
        
    def addToLibrary(self):
        add_json = self.provider.createEntry(self)

    def fetchMissingData(self):
        try:
            if self.provider is not None:
              lookup_json = self.provider.lookupMedia(self)
              if lookup_json is not None:
                self._setMissingData(lookup_json)
        except requests.exceptions.HTTPError as e:
            self.log.debug(f"Request exception: {e}")
            self._setMissingData(None)
            
        
    def _setMissingData(self, data):
        #The media lookup returns a list of results, but we only need the first since we are explicitly
        #querying the id

        if data is None:
            print(f"No data to set for {self}")
            return
    
        item = data[0]        
        self.log.info(f"{item} media data")

        if not self.image:
           self.image = item["images"]

        if self.type == APIObjectType.Movie.value:
            self.titleSlug = item["titleSlug"]
            self.qualityProfile = item["qualityProfileId"]
            self.year = item["year"]    
            self.tmdbId = item["tmdbId"]    
            self.overview = item["overview"]
            self.rating = item["ratings"]
        elif self.type == APIObjectType.Show.value:
            self.titleSlug = item["titleSlug"]
            self.seasons = item["seasons"]
            self.qualityProfile = item["qualityProfileId"]
            self.year = item["year"]
            self.rating = item["ratings"]
        elif self.type == APIObjectType.Episode.value:
             self.titleSlug = item["titleSlug"]
             self.qualityProfile = item["qualityProfileId"]
             self.year = item["year"]
             self.tmdbId = item["tmdbId"]
             self.overview = item["overview"]
             self.rating = item["ratings"]
        else:
            print(f"Don't know how to set data for {self.title} - {self.type}") 

    def _extractGUID(self,guid):
        if not guid:
            return
        match = re.search(r'\d+', guid)
        if match:
        #Force padding imdb ids or else anything with leading zeroes fails
            padded = str(match.group().zfill(7))
            self.log.debug(f"Found guid {padded} for {self.title}")
            return padded

