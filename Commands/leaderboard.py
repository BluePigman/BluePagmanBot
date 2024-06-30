def reply_with_leaderboard(self, message):
    top_users = self.users.find().sort([('points', -1)]).limit(5)
    leaderboard_message = "Leaderboard: "
    for idx, user in enumerate(top_users, start=1):
        leaderboard_message += f"{idx}. @{user['user']} - {user['points']}   "
    self.send_privmsg(message['command']['channel'], leaderboard_message)