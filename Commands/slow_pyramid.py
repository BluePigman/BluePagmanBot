import time
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_slow_pyramid(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    if cmd.params and len(cmd.params.split()) > 1:
        args = cmd.params.split()
        emote = args[0]
        width = args[1]
        if not width.isnumeric():
            text = f"Width must be an integer. Usage: {self.prefix}slow_pyramid {{name}} {{width}}"
            self.send_privmsg(cmd.channel, text)
            return
        width = int(width)
        if len(emote) * width + width - 1 < 500:
            text = ''
            for _ in range(width):  # go up
                text += (emote + ' ')
                self.send_privmsg(cmd.channel, text)
                time.sleep(1.6)
            for _ in range(width-1):  # go down
                text = text.rsplit(emote, 1)[0]
                self.send_privmsg(cmd.channel, text)
                time.sleep(1.6)
        else:
            text = 'Pyramid is too large to be displayed in chat. Use \
            a smaller pyramid width.'
            self.send_privmsg(cmd.channel, text)

    else:
        text = f"Usage: {self.prefix}slow_pyramid {{name}} {{width}}"
        self.send_privmsg(cmd.channel, text)
