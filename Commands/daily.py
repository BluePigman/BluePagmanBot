import datetime
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_daily(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    user_data = self.users.find_one({'user': cmd.nick})
    if not user_data: # add new user
        self.users.insert_one({'user': cmd.nick , 'last_claimed':datetime.datetime.now(), 'points': 100 })
        self.send_privmsg(cmd.channel, f"{cmd.username}, your daily reward is 100 Pigga Coins. Come back tomorrow for more!")
    else: # check time
        if 'last_claimed' not in user_data:
            self.users.update_one({'user': cmd.nick}, {'$set': {'last_claimed': datetime.datetime.now()}, '$inc': {'points': 100}})
            self.send_privmsg(cmd.channel, f"{cmd.username}, your daily reward is 100 Pigga Coins. Come back tomorrow for more!")
            return
        last_claimed = user_data['last_claimed']
        time_diff = datetime.datetime.now() - last_claimed
        if time_diff.days >= 1: # give reward
            self.users.update_one({'user': cmd.nick}, {'$set': {'last_claimed': datetime.datetime.now()}, '$inc': {'points': 100}})
            self.send_privmsg(cmd.channel, f"{cmd.username}, your daily reward is 100 Pigga Coins. Come back tomorrow for more!")
        else:
            remaining_time = datetime.timedelta(days=1) - time_diff
            remaining_hours = remaining_time.seconds // 3600
            remaining_minutes = (remaining_time.seconds % 3600) // 60
            remaining_seconds = remaining_time.seconds % 60

            t = "You have already collected your dailies today. Come back in {}h, {}m, {}s.".format(
                remaining_hours, remaining_minutes, remaining_seconds)

            self.send_privmsg(cmd.channel, t)