import time
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_help_ascii(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    help_msg = f"usage: {self.prefix}ascii " + \
        "[Emote] [-w] [-h] [-r {90,180,270}] [-tr] [-d] [-b] [-e] [-i] [-g] [-t]"
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
    -t {text} Text to print below the ASCII.""".replace("\n", " ")

    self.send_privmsg(cmd.channel, help_msg)
    time.sleep(1.1)
    self.send_privmsg(cmd.channel, help_msg2)
