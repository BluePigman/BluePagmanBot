from Utils.utils import check_cooldown, fetch_cmd_data

def reply_with_bot(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    text = 'BluePAGMANBot is a bot made by @Bluepigman5000 in Python. \
    It has some basic commands, and can run a game of chess in chat \
    between two different players. It is currently running on a VM on Google Cloud Compute Engine.'

    self.send_privmsg(cmd.channel, text)