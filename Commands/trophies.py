import time

def reply_with_trophies(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
        self.cooldown):
        self.state[message.user] = time.time()

        if not message.text_args:
            user_data = self.users.find_one({'user': message.user})
            if not user_data or 'trophies' not in user_data: 
                m = f"@{message.user}, you do not have any trophies in your collection. Buy some in the shop."
                self.send_privmsg(message.channel, m)
                return
            trophies_count = user_data.get('trophies', 0)
            if trophies_count <= 0:
                m = f"@{message.user}, you don't have any trophies in your collection. Buy some in the shop."
                self.send_privmsg(message.channel, m)
                return
            else:
                trophy_string = f"🏆 " * trophies_count
                m = f"@{message.user}, you have {trophies_count} trophies in your collection. {trophy_string}"
                return

        else: # search a user's trophies count.
            searchUser = message.text_args[0]
            if '\U000e0000' in searchUser:
                searchUser = searchUser.replace('\U000e0000', '')
            if '@' in searchUser:
                searchUser = searchUser.replace('@', '')
            
            user_data = self.users.find_one({'user': searchUser.lower()})
            if not user_data or 'trophies' not in user_data:
                self.send_privmsg(message.channel, f'@{message.user}, That user does not have any trophies.')
            else:
                trophy_string = f"🏆 " * user_data['trophies']
                self.send_privmsg(message.channel, f'@{message.user}, {searchUser} has {user_data["trophies"]} trophies in their \
                                  collection. {trophy_string}')
