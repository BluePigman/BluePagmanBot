from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_shop(self, message):
    cmd = fetch_cmd_data(self, message)

    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return
    
    query = cmd.params

    if not query:
        m = "Available for sale: Timeout (100 Coins): Timeout a user (not a moderator) for 10 seconds. | Trophy (1000 Coins): Add a trophy to your collection. 🏆"
        self.send_privmsg(cmd.channel, m)
        return
   
    if query.startswith("buy"):
        args = query.split(" ")
        if len(args) != 2:
            m = "Usage: shop buy <item>"
            self.send_privmsg(cmd.channel, m)
            return

        item = args[1].lower() 
        user_data = self.users.find_one({'user': cmd.nick})
        if not user_data: 
            m = f"{cmd.username}, you do not have any Pigga Coins. Use the daily command."
            self.send_privmsg(cmd.channel, m)
            return

        user_points = user_data['points']

        if item == "timeout":
            if user_points < 100:
                m = f"{cmd.username}, you don't have enough Pigga Coins to buy a Timeout."
                self.send_privmsg(cmd.channel, m)
                return
            # Process the purchase
            # Deduct points, update database, send message
            self.users.update_one({'user': cmd.nick}, {'$inc': {'points': -100}})
            self.users.update_one({'user': cmd.nick}, {'$inc': {'timeout': 1}})
            m = f"{cmd.username}, you bought a Timeout for 100 Pigga Coins! Use it wisely."
            self.send_privmsg(cmd.channel, m)

        elif item == "trophy":
            if user_points < 1000:
                m = f"{cmd.username}, you don't have enough Pigga Coins to buy a Trophy."
                self.send_privmsg(cmd.channel, m)
                return

            m = f"{cmd.username}, you bought Trophy for 1000 Pigga Coins! 🏆"
            self.users.update_one({'user': cmd.nick}, {'$inc': {'points': -1000}})
            self.users.update_one({'user': cmd.nick}, {'$inc': {'trophies': 1}})
            self.send_privmsg(cmd.channel, m)

        else:
            m = f"{cmd.username}, that item is not available in the shop."
            self.send_privmsg(cmd.channel, m)