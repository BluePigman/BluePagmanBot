import time


def reply_with_source_code(self, message):
        if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
                self.cooldown):
            self.state[message['source']['nick']] = time.time()
            text = 'Source code: https://github.com/BluePigman/BluePagmanBot'
            self.send_privmsg(message['command']['channel'], text)
