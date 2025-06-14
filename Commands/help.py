from Utils.utils import check_cooldown, fetch_cmd_data


def list_commands(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    custom_cmd_names = list(self.custom_commands.keys())
    all_cmd_names = [
        self.prefix + cmd
        for cmd in custom_cmd_names
    ]
    text = "" f"@{message['tags']['display-name']}, Commands: " + ' '.join(all_cmd_names)
    self.send_privmsg(cmd.channel, text)