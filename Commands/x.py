from Utils.utils import fetch_cmd_data, check_cooldown


def reply_with_x(self, message):
    cmd = fetch_cmd_data(self, message)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    if not cmd.params:
        m = "Please provide a Twitter link, or reply to a message containing a Twitter link with this command."
        self.send_privmsg(cmd.channel, m)
        return
    
    if "twitter.com/" in cmd.params:
        cmd.params = cmd.params.replace("twitter.com", "x.com")
    if "x.com" in cmd.params:
        cmd.params = cmd.params.replace("x.com", "nitter.net")
        self.send_privmsg(cmd.channel, cmd.params)