from .task_type import TaskType

STARTING = "Starting"
CONNECTING = "Connecting"
SCANNING= "Scanning"
COMPARING= "Comparing"
FINALIZING = "Finalizing" 



class ComparisonTask(TaskType):
    
    def __init__(self):
        super().__init__()
        self._steps = 8

