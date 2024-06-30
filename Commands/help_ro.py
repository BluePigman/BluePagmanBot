import time


def reply_with_help_ro(self, message):
    text = (f"@{message['source']['nick']}, Gets a random opening. You can add -b or -w \
        for a specific side, and/or add a name for search. e.g. {self.command_prefix}ro King's Indian \
            Defense -w")
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        self.send_privmsg(message['command']['channel'], text)