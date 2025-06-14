from Utils.utils import check_cooldown, fetch_cmd_data
import Utils.newsCommands as newsCommands


def reply_with_help_news(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    self.send_privmsg(cmd.channel, newsCommands.get_help_text())