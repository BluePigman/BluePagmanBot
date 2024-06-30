import datetime
import time


def reply_with_daily(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        user_data = self.users.find_one({'user': message['source']['nick']})
        if not user_data: # add new user
            self.users.insert_one({'user': message['source']['nick'] , 'last_claimed':datetime.datetime.now(), 'points': 100 })
            self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, your daily reward is 100 Pigga Coins. Come back tomorrow for more!")
        else: # check time
            last_claimed = user_data['last_claimed']
            time_diff = datetime.datetime.now() - last_claimed
            if time_diff.days >= 1: # give reward
                self.users.update_one({'user': message['source']['nick']}, {'$set': {'last_claimed': datetime.datetime.now()}, '$inc': {'points': 100}})
                self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, your daily reward is 100 Pigga Coins. Come back tomorrow for more!")
            else:
                remaining_time = datetime.timedelta(days=1) - time_diff
                remaining_hours = remaining_time.seconds // 3600
                remaining_minutes = (remaining_time.seconds % 3600) // 60
                remaining_seconds = remaining_time.seconds % 60

                t = "You have already collected your dailies today. Come back in {}h, {}m, {}s.".format(
                    remaining_hours, remaining_minutes, remaining_seconds)

                self.send_privmsg(message['command']['channel'], t)