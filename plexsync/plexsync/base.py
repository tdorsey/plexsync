
import configparser
import enum
import logging
import os
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
        if not os.path.exists(directory):
          self.log.info(f"Creating {directory}")
          os.makedirs(directory) 

#Create a module level instance of settings

base = Base()

this = sys.modules[__name__]
this.settings = None
this.settings = base.getSettings()
