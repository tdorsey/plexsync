
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

def getAccount(username=None, password=None):
        username = username or configParser.get("auth", "myplex_username")
        password = password or configParser.get("auth", "myplex_password")
        return MyPlexAccount(username, password)


CONFIG_PATH = str(os.path.join('/config', 'config.ini'))
log = logging.getLogger("plexsync")
configParser = configparser.SafeConfigParser()
log.info(f"Reading configuration from {CONFIG_PATH}")
settings =  configParser.read(CONFIG_PATH)

log.info("Getting Account")
account = getAccount()

class Base:
    def __init__(self):
            self.settings = configParser
            self.log = log

    def getSettings(self):
        return settings

    def getAccount(self,username=None, password=None):
        return account or getAccount(username, password)

    def writeSettings(self,settings):
        with open(CONFIG_PATH, 'w') as config_file:
           configParser.write(config_file)

    def create_dir(self, directory):
        p =  Path(directory)
        if not p.exists():
           try:
             p.mkdir(parents=True)
             shutil.chown(p,user="plexsync",group="plexsync")
           except Exception as e:
            self.log.error(json.dumps(repr(e)))
            raise
