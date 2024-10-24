import time


def reply_with_slow_pyramid(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        if message['command']['botCommandParams'] and len(message['command']['botCommandParams'].split()) > 1:
            args = message['command']['botCommandParams'].split()
            emote = args[0]
            width = args[1]
            if not width.isnumeric():
                text = f"Width must be an integer. Usage: {self.prefix}slow_pyramid {{name}} {{width}}"
                self.send_privmsg(message['command']['channel'], text)
                return
            width = int(width)
            if len(emote) * width + width - 1 < 500:
                text = ''
                for _ in range(width):  # go up
                    text += (emote + ' ')
                    self.send_privmsg(message['command']['channel'], text)
                    time.sleep(1.6)
                for _ in range(width-1):  # go down
                    text = text.rsplit(emote, 1)[0]
                    self.send_privmsg(message['command']['channel'], text)
                    time.sleep(1.6)
            else:
                text = 'Pyramid is too large to be displayed in chat. Use \
                a smaller pyramid width.'
                self.send_privmsg(message['command']['channel'], text)

        else:
            text = f"Usage: {self.prefix}slow_pyramid {{name}} {{width}}"
            self.send_privmsg(message['command']['channel'], text)
