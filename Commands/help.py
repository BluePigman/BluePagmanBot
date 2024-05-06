import time


def list_commands(self, message):
    custom_cmd_names = list(self.custom_commands.keys())
    all_cmd_names = [
        self.command_prefix + cmd
        for cmd in custom_cmd_names
    ]
    text = "" f'@{message.user}, Commands: ' + ' '.join(all_cmd_names)
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        self.send_privmsg(message.channel, text)