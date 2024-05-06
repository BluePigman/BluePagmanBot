import time

# https://stackoverflow.com/q/6266727
def reply_with_pyramid(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        if len(message.text_args) > 1 and message.text_args[1].isnumeric():
            emote = message.text_args[0]
            width = int(message.text_args[1])
            if len(emote) * width + width - 1 < 500:
                text = ''
                for x in range(width):  # go up
                    text += (emote + ' ')
                    self.send_privmsg(message.channel, text)
                    time.sleep(0.1)
                for y in range(width - 1):  # go down
                    text = text.rsplit(emote, 1)[0]
                    self.send_privmsg(message.channel, text)
                    time.sleep(0.1)
            else:
                text = 'Pyramid is too large to be displayed in chat. Use \
                a smaller pyramid width.'
                self.send_privmsg(message.channel, text)

        else:
            text = f'Width must be an integer. Usage: {self.command_prefix}pyramid {{name}} {{width}}'
            self.send_privmsg(message.channel, text)