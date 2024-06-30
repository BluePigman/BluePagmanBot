import time

def reply_with_trophies(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
        self.cooldown):
        self.state[message['source']['nick']] = time.time()

        if not message['command']['botCommandParams']:
            user_data = self.users.find_one({'user': message['source']['nick']})
            if not user_data or 'trophies' not in user_data: 
                m = f"@{message['tags']['display-name']}, you do not have any trophies in your collection. Buy some in the shop."
                self.send_privmsg(message['command']['channel'], m)
                return
            trophies_count = user_data.get('trophies', 0)
            if trophies_count <= 0:
                m = f"@{message['tags']['display-name']}, you don't have any trophies in your collection. Buy some in the shop."
                self.send_privmsg(message['command']['channel'], m)
                return
            else:
                trophy_string = f"🏆 " * trophies_count
                m = f"@{message['tags']['display-name']}, you have {trophies_count} trophies in your collection. {trophy_string}"
                return

        else: # search a user's trophies count.
            searchUser = message['command']['botCommandParams']
            if '\U000e0000' in searchUser:
                searchUser = searchUser.replace('\U000e0000', '')
            if '@' in searchUser:
                searchUser = searchUser.replace('@', '')
            
            user_data = self.users.find_one({'user': searchUser.lower()})
            if not user_data or 'trophies' not in user_data:
                self.send_privmsg(message['command']['channel'], f"@{message['tags']['display-name']}, That user does not have any trophies.")
            else:
                trophy_string = f"🏆 " * user_data['trophies']
                self.send_privmsg(message['command']['channel'], f"@{message['tags']['display-name']}, {searchUser} has {user_data['trophies']} trophies in their \
                                  collection. {trophy_string}")
