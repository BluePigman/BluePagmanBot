import time


def list_commands(self, message):
    custom_cmd_names = list(self.custom_commands.keys())
    all_cmd_names = [
        self.prefix + cmd
        for cmd in custom_cmd_names
    ]
    text = "" f"@{message['tags']['display-name']}, Commands: " + ' '.join(all_cmd_names)
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        self.send_privmsg(message['command']['channel'], text)
