import datetime
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_date(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    text = f"{cmd.username}, the date is {formatted_date} EST."
    self.send_privmsg(cmd.channel, text)