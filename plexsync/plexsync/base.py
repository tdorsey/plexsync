import configparser
import enum
import os
import sys

from pathlib import Path

CONFIG_PATH = str(os.path.join('/config', 'config.ini'))

class APIObjectType(enum.Enum):
    Show = 1
    Movie = 2

def dump(obj):
    for attr in dir(obj):
        if hasattr(obj, attr):
            print("obj.%s = %s" % (attr, getattr(obj, attr)))

def getSettings():
    settings = configparser.ConfigParser()
    print(f"Reading configuration from {CONFIG_PATH} ")
    settings.read(CONFIG_PATH)
    return settings

def writeSettings(settings):
    with open(CONFIG_PATH, 'w') as config_file:
        settings.write(config_file)



#Create a module level instance of settings
this = sys.modules[__name__]
this.settings = None
this.settings = getSettings()
