import Utils.chessCommands as chessCommands
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_random_opening(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if cmd.params:
        if '-w' in cmd.params or '-b' in cmd.params:
            side = 'w' if '-w' in cmd.params else 'b'
            name = cmd.params.replace(f'-{side}', '')
            opening = chessCommands.getRandomOpeningSpecific(name, side)
        else:
            opening = chessCommands.getRandomOpeningSpecific(cmd.params)
    else:
        opening = chessCommands.getRandomOpening()

    self.send_privmsg(cmd.channel, f"{cmd.username}, {opening}")