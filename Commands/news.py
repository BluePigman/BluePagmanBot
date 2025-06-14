import Utils.newsCommands as newsCommands
from Utils.utils import check_cooldown, fetch_cmd_data, encode_str


def reply_with_news(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    try:
        if cmd.params:
            m = newsCommands.get_random_news_item(encode_str(cmd.params))
        else:
            m = newsCommands.get_random_news_item()
        self.send_privmsg(cmd.channel, m) 
    except Exception as e:
        print(e)
        self.send_privmsg(cmd.channel, f"Error: {str(e)[:300]}")