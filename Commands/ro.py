import time

import chessCommands


def reply_with_random_opening(self, message):

    text = f'@{message.user}, '

    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()

        # if args present
        if (message.text_args):

            if '-w' in message.text_args:
                # get opening for white
                side = 'w'
                message.text_args.remove('-w')
                name = " ".join(message.text_args)
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message.channel, text + opening)

            elif '-b' in message.text_args:
                # get opening for black
                side = 'b'
                message.text_args.remove('-b')
                name = " ".join(message.text_args)
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(
                    name, side)
                self.send_privmsg(message.channel, text + opening)

            else:  # get opening for specified search term
                name = " ".join(message.text_args)
                if '\U000e0000' in name:
                    name = name.replace('\U000e0000', '')

                opening = chessCommands.getRandomOpeningSpecific(name)
                self.send_privmsg(message.channel, text + opening)

        else:  # No arguments
            opening = chessCommands.getRandomOpening()
            self.send_privmsg(message.channel, text + opening)