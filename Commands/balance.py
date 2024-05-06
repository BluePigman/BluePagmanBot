import time


def reply_with_balance(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        if message.text_args:
            searchUser = message.text_args[0]
            if '\U000e0000' in searchUser:
                searchUser = searchUser.replace('\U000e0000', '')
            if '@' in searchUser:
                searchUser = searchUser.replace('@', '')
            user_data = self.users.find_one({'user': searchUser.lower()})
            if not user_data:
                self.send_privmsg(message.channel, f'@{message.user}, That user is not in the database.')
            else:
                self.send_privmsg(message.channel, f'@{message.user}, {searchUser} has {user_data["points"]} Pigga Coins.')


        else:
            user_data = self.users.find_one({'user': message.user})
            if not user_data:
                self.send_privmsg(message.channel, f'@{message.user}, you do not have any Pigga Coins. Use the daily command.')
            else:
                self.send_privmsg(message.channel, f'@{message.user}, you have {user_data["points"]} Pigga Coins.')        
