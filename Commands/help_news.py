import time
import newsCommands


def reply_with_help_news(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        self.send_privmsg(message.channel, newsCommands.get_help_text())