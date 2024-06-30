import time

def reply_with_help_ascii(self, message):
    help_msg = f"usage: {self.command_prefix}ascii " + "[Emote] [-w] [-h] [-r {90,180,270}] [-tr] [-d] [-b] [-e] [-i] [-g] [-t]"
    help_msg2 = """Generate ascii art from emote link.
    Optional arguments:
    -w {int} width of ascii
    -h {int} height of ascii
    -r {90,180,270} rotate ascii clockwise
    -tr {0-255} level to apply threshold dithering
    -d Use Floyd-Steinberg dithering.
    -b Remove transparent background.
    -e Keep empty characters.
    -i Invert the end result.
    -g Use multiple frames of the first gif provided.
    -t {text} Text to print below the ASCII. (TODO)""".replace("\n", " ")

    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        self.send_privmsg(message['command']['channel'], help_msg)
        time.sleep(0.69)
        self.send_privmsg(message['command']['channel'], help_msg2)