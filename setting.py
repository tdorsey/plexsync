class Setting():
    def __init__(self, key, section, prompt):
        self.key = key
        self.value = None 
        self.prompt = prompt
        self.section = section

    def write(self):
            print(f"setting {self.key} in {self.section}")

            user_input = input(self.prompt)
            self.value = str(user_input)

            settings.set(_section, setting.key, setting.value)
            writeSettings(settings)
            return setting.value


