import time

import Utils.chessCommands as chessCommands


def reply_with_random_opening(self, message):

    text = f"@{message['tags']['display-name']}, "

    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        args = message['command']['botCommandParams']
        # if args present
        if (args):

            if '-w' in args:
                # get opening for white
                side = 'w'
                name = args.replace('-w', '')
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message['command']['channel'], text + opening)

            elif '-b' in args:
                # get opening for black
                side = 'b'
                name = args.replace('-w', '')
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message['command']['channel'], text + opening)

            else:  # get opening for specified search term
                name = args
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(name)
                self.send_privmsg(message['command']['channel'], text + opening)

        else:  # No arguments
            opening = chessCommands.getRandomOpening()
            self.send_privmsg(message['command']['channel'], text + opening)