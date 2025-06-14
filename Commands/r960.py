from Utils.utils import check_cooldown, fetch_cmd_data
import Utils.chessCommands as chessCommands


def reply_with_random960(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    opening = chessCommands.getRandom960()
    self.send_privmsg(cmd.channel, opening)