from base import *

settings = getSettings()

class Setting():
    def __init__(self, key, section, prompt):
        self.key = key
        self.value = None 
        self.prompt = prompt
        self.section = section

    def write(self):
            print(f"setting {self.key} in {self.section}")

            if not self.value:
                user_input = input(self.prompt)
                self.value = str(user_input)
            settings.set(self.section, self.key, self.value)
            writeSettings(settings)
            return self.value


