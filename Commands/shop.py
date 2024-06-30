import time


def reply_with_shop(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
        self.cooldown):
        self.state[message['source']['nick']] = time.time()

        query = message['command']['botCommandParams']

        print(query)
        if not query:
            # Default response if the command is not recognized
            m = "Available for sale: Timeout (100 Coins): Timeout a user (not a moderator) for 10 seconds.| Trophy (1000 Coins): Add a trophy to your collection. 🏆"
            self.send_privmsg(message['command']['channel'], m)
            return
        
        if '\U000e0000' in query:
                query = query.replace('\U000e0000', '')
        

        if query.startswith("buy"):
            args = query.split(" ")
            if len(args) != 2:
                m = "Usage: shop buy <item>"
                self.send_privmsg(message['command']['channel'], m)
                return

            item = args[1].lower() 
            user_data = self.users.find_one({'user': message['source']['nick']})
            if not user_data: 
                m = f"@{message['tags']['display-name']}, you do not have any Pigga Coins. Use the daily command."
                self.send_privmsg(message['command']['channel'], m)
                return

            user_points = user_data['points']

            if item == "timeout":
                if user_points < 100:
                    m = f"@{message['tags']['display-name']}, you don't have enough Pigga Coins to buy a Timeout."
                    self.send_privmsg(message['command']['channel'], m)
                    return
                # Process the purchase
                # Deduct points, update database, send message
                self.users.update_one({'user': message['source']['nick']}, {'$inc': {'points': -100}})
                self.users.update_one({'user': message['source']['nick']}, {'$inc': {'timeout': 1}})
                m = f"@{message['tags']['display-name']}, you bought a Timeout for 100 Pigga Coins! Use it wisely."
                self.send_privmsg(message['command']['channel'], m)
                return

            elif item == "trophy":
                if user_points < 1000:
                    m = f"@{message['tags']['display-name']}, you don't have enough Pigga Coins to buy a Trophy."
                    self.send_privmsg(message['command']['channel'], m)
                    return
                # Process the purchase
                # Deduct points, update database, send message
                m = f"@{message['tags']['display-name']}, you bought Trophy for 1000 Pigga Coins! 🏆"
                self.users.update_one({'user': message['source']['nick']}, {'$inc': {'points': -1000}})
                self.users.update_one({'user': message['source']['nick']}, {'$inc': {'trophies': 1}})
                self.send_privmsg(message['command']['channel'], m)
                return

            else:
                m = f"@{message['tags']['display-name']}, that item is not available in the shop."
                self.send_privmsg(message['command']['channel'], m)
                return