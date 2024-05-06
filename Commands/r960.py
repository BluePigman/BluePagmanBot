import time

import chessCommands


def reply_with_random960(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        opening = chessCommands.getRandom960()
        self.send_privmsg(message.channel, opening)