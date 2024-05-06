import time


def reply_with_source_code(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            text = 'Source code: https://github.com/BluePigman/BluePagmanBot'
            self.send_privmsg(message.channel, text)
