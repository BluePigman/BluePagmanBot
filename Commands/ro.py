import time

import chessCommands


def reply_with_random_opening(self, message):

    text = f"@{message['source']['nick']}, "

    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()

        # if args present
        if (message['command']['botCommandParams']):

            if '-w' in message['command']['botCommandParams']:
                # get opening for white
                side = 'w'
                message['command']['botCommandParams'].remove('-w')
                name = " ".join(message['command']['botCommandParams'])
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message['command']['channel'], text + opening)

            elif '-b' in message['command']['botCommandParams']:
                # get opening for black
                side = 'b'
                message['command']['botCommandParams'].remove('-b')
                name = " ".join(message['command']['botCommandParams'])
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message['command']['channel'], text + opening)

            else:  # get opening for specified search term
                name = " ".join(message['command']['botCommandParams'])
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(name)
                self.send_privmsg(message['command']['channel'], text + opening)

        else:  # No arguments
            opening = chessCommands.getRandomOpening()
            self.send_privmsg(message['command']['channel'], text + opening)