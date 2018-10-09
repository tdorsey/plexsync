from enum import Enum
from collections import namedtuple

class MessageLevels(Enum):
   
    PRIMARY = "primary"
    SECONDARY = "secondary"
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    SUCCESS = "success"

class States(Enum):

    PENDING = "Pending..."
    FAILURE = "Failure"
    SUCCESS =  "Success"

states = [States.PENDING, States.FAILURE, States.SUCCESS]
message_levels = [MessageLevels.PRIMARY, MessageLevels.SECONDARY, MessageLevels.INFO, MessageLevels.WARNING, MessageLevels.DANGER, MessageLevels.SUCCESS]

class TaskType:
    def __init__(self):
        _steps = 0
        _message_levels = message_levels
        _states = states
   
    @property
    def steps(self):
        return self._steps

    @property
    def messageLevel(self):
        return self._message_levels

    @property
    def state(self):
        return self._states


