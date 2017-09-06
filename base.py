import configparser
import enum
import os
import sys

from pathlib import Path

class APIObjectType(enum.Enum):
    Show = 1
    Movie = 2

def dump(obj):
    for attr in dir(obj):
        if hasattr(obj, attr):
            print("obj.%s = %s" % (attr, getattr(obj, attr)))

def getSettings():
        settings = configparser.ConfigParser()
        CONFIG_PATH = str(os.path.join(Path.home(), '.config', 'plexsync', 'config.ini'))
        print(f"Reading configuration from {CONFIG_PATH} ")
        settings.read(CONFIG_PATH)        
        return settings




#Create a module level instance of settings
this = sys.modules[__name__]
this.settings = None
this.settings = getSettings()

