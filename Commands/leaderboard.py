from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_leaderboard(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return
    
    top_users = self.users.find().sort([('points', -1)]).limit(5)
    leaderboard_message = "Leaderboard: "
    for idx, user in enumerate(top_users, start=1):
        leaderboard_message += f"{idx}. @{user['user']} - {user['points']}"
    self.send_privmsg(cmd.channel, leaderboard_message)