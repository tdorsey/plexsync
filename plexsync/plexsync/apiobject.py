import logging
import re
import requests
import time
import urllib

from plexapi.video import Video

def _hash(self):
    return hash(self.title) 

def _eq(self, other):
    return (self.title == other.title)     

Video.__hash__ = _hash
Video.__eq__ = _eq

from plexsync.base import *
from plexsync.thirdparty import ThirdParty, ThirdPartyService

show_provider = ThirdParty(ThirdPartyService.Show)
movie_provider = ThirdParty(ThirdPartyService.Movie)

class APIObjectType(enum.Enum):
    Show = "show"
    Movie = "movie"
    Episode = "episode"

class APIObject(Video):
    def __init__(self, video):
        self.log = logging.getLogger('plexsync')
        if video.type == "episode":
           self.title = video.show().title
           self.type = APIObjectType.Episode
           self.provider = show_provider
           self.guid = video.show().guid
        elif video.type == "show":
            self.title = video.title
            self.type = APIObjectType.Show
            self.provider = show_provider
            self.guid = video.guid
            self.overview = video.summary
            self.rating = video.rating
            self.year = video.year
            #plex api doesn't support poster directly, just the banner, but it's a plex structured url, so swap it.
            if video.banner is None:
              self.log.debug(f"no banner: Falling back to {video.artUrl}")
              self.image= video.artUrl
            else:
              self.log.debug(f"Switching banner to poster {video.banner}")
              self.image =  video.url(video.banner).replace("banner", "poster")
        elif video.type == "movie":
            self.title = video.title
            self.type = APIObjectType.Movie
            self.provider = movie_provider
            self.guid = video.guid
            self.image = video.artUrl
        else:
            self.log.debug(f"Unable to determine Object Type for {video}")
            return None
        self.search_term = self._createSearchTerm()
        self.qualityProfileId = None
        self.titleSlug = None
        self.seasons = []
        self.librarySectionID = video.librarySectionID
        self.downloadURL = self._getDownloadURL(video)
      
    def isMovie(self):
        return self.type == APIObjectType.Movie

    def isShow(self):
        return self.type == APIObjectType.Show
    
    def isEpisode(self):
        return self.type == APIObjectType.Episode

    def _createSearchTerm(self):
        shortGUID = self._extractGUID(self.guid)
        if self.isMovie():
            return str(f"imdb:tt{shortGUID}")
        elif self.isShow():
            return str(f"tvdb:{shortGUID}")

    def _getDownloadURL(self, video):
        if self.isMovie():
          for part in video.iterParts():
        #We do this manually since we dont want to add a progress to Episode etc
              url = video._server.url('%s?download=1' %part.key)
          return url
        elif self.isShow():
             episode =  video.episodes()[0]
             for part in episode.iterParts():
                 url = episode._server.url('%s?download-1' %part.key)
                 return url
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
        try:
            lookup_json = self.provider.lookupMedia(self)
            if lookup_json:
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

        if self.isMovie():
            self.titleSlug = item["titleSlug"]
            self.qualityProfile = item["qualityProfileId"]
            self.year = item["year"]    
            self.tmdbId = item["tmdbId"]    
            self.overview = item["overview"]
            self.rating = item["ratings"]
        elif self.isShow():
            self.titleSlug = item["titleSlug"]
            self.seasons = item["seasons"]
            self.qualityProfile = item["qualityProfileId"]
            self.year = item["year"]
            self.rating = item["ratings"]
        elif self.isEpisode():
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

