import time


def reply_with_help_ro(self, message):
    text = (f"@{message.user}, Gets a random opening. You can add -b or -w \
        for a specific side, and/or add a name for search. e.g. {self.command_prefix}ro King's Indian \
            Defense -w")
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        self.send_privmsg(message.channel, text)