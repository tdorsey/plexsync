
import configparser
import enum
import json
import logging
import grp
import os
import pwd
import sys


from pathlib import Path

CONFIG_PATH = str(os.path.join('/config', 'config.ini'))

def dump(obj):
    for attr in dir(obj):
        if hasattr(obj, attr):
            print("obj.%s = %s" % (attr, getattr(obj, attr)))

class Base:
    def __init__(self):
        self.log = logging.getLogger("plexsync")
        self.settings = self.getSettings() 

    def getSettings(self):
          config = configparser.SafeConfigParser()
          self.log.info(f"Reading configuration from {CONFIG_PATH}")
          config.read(CONFIG_PATH)  
          return config

    def writeSettings(self,settings):
        with open(CONFIG_PATH, 'w') as config_file:
            self.settings.write(config_file)

    def create_dir(self, directory):
        uid = pwd.getpwnam("plexsync").pw_uid
        self.log.error("got uid {uid}") 
        gid = grp.getgrgid("plexsync").gr_gid
        self.log.error("got gid {gid}") 
        p =  Path(directory)
        if not p.exists():
           try:
             p.mkdir(parents=True)
             self.log.warn(f"chowning {p} to {uid}:{gid}")
             os.chown(p,uid,gid)
           except Exception as e:
            self.log.error(json.dumps(repr(e)))
            raise
