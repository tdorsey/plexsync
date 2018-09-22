
import configparser
import enum
import json
import logging
import os
import grp
import shutil
import sys

from pathlib import Path

from plexapi.myplex import MyPlexAccount

def dump(obj):
    for attr in dir(obj):
        if hasattr(obj, attr):
            print("obj.%s = %s" % (attr, getattr(obj, attr)))

def getAccount(self, username=None, password=None, token=None):
            if token:
              self.account = MyPlexAccount(token=token) 
            else:
               username = username or configParser.get("auth", "myplex_username")
               password = password or configParser.get("auth", "myplex_password")
               self.account = MyPlexAccount(username, password)
            return self.account


CONFIG_PATH = str(os.path.join('/config', 'config.ini'))
log = logging.getLogger("plexsync")
configParser = configparser.SafeConfigParser()
log.info(f"Reading configuration from {CONFIG_PATH}")
settings =  configParser.read(CONFIG_PATH)

log.info("Getting Account")

class Base:
    def __init__(self):
            self.settings = configParser
            self.log = log
            self.account = getAccount(self)

    def getSettings(self):
        return settings

    def getAccount(self,username=None, password=None, token=None):
        return self.account or getAccount(token=token) or getAccount(username, password)

    def writeSettings(self,settings):
        with open(CONFIG_PATH, 'w') as config_file:
           configParser.write(config_file)

    def create_dir(self, directory):
           try:
             p = Path(directory)
             p.mkdir(parents=True, exist_ok=True)
             shutil.chown(p,user="plexsync",group="plexsync")
             return p
           except Exception as e:
            self.log.exception(e)
            raise
