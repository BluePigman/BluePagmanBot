from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_help_ro(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    text = (f"{cmd.username}, Gets a random opening. You can add -b or -w \
        for a specific side, and/or add a name for search. e.g. {self.prefix}ro King's Indian \
            Defense -w")

    self.send_privmsg(cmd.channel, text)
