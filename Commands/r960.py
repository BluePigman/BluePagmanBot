import time
import Utils.chessCommands as chessCommands


def reply_with_random960(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        opening = chessCommands.getRandom960()
        self.send_privmsg(message['command']['channel'], opening)