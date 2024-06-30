import time


def reply_with_balance(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        if message['command']['botCommandParams']:
            searchUser = message['command']['botCommandParams']
            if '\U000e0000' in searchUser:
                searchUser = searchUser.replace('\U000e0000', '')
            if '@' in searchUser:
                searchUser = searchUser.replace('@', '')
            user_data = self.users.find_one({'user': searchUser.lower()})
            if not user_data:
                self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, That user is not in the database.")
            else:
                self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, {searchUser} has {user_data['points']} Pigga Coins.")


        else:
            user_data = self.users.find_one({'user': message['source']['nick']})
            if not user_data:
                self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, you do not have any Pigga Coins. Use the daily command.")
            else:
                self.send_privmsg(message['command']['channel'], f"@{message['source']['nick']}, you have {user_data['points']} Pigga Coins.")        
