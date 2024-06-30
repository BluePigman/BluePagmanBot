import time


def reply_with_bot(self, message):

    text = 'BluePAGMANBot is a bot made by @Bluepigman5000 in Python. \
    It has some basic commands, and can run a game of chess in chat \
    between two different players. It is currently running on a VM on Google Cloud Compute Engine.'

    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        self.send_privmsg(message['command']['channel'], text)