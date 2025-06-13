from Utils.utils import check_cooldown, fetch_cmd_data, clean_str


def reply_with_trophies(self, message):
    cmd = fetch_cmd_data(self, message)
    
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown):
        return

    if not cmd.params:
        user_data = self.users.find_one({'user': cmd.nick})
        trophies_count = user_data.get('trophies', 0) if user_data else 0

        if trophies_count == 0:
            m = f"{cmd.username}, you do not have any trophies in your collection. Buy one with {self.prefix}shop buy trophy"
        else:
            trophy_string = "🏆 " * trophies_count
            m = f"{cmd.username}, you have {trophies_count} trophies in your collection. {trophy_string}"

        self.send_privmsg(cmd.channel, m)
        return

    else: # search a user's trophies count.
        searchUser = clean_str(cmd.params, ["@", ","])
        
        user_data = self.users.find_one({'user': searchUser.lower()})
        if not user_data or 'trophies' not in user_data:
            self.send_privmsg(cmd.channel, f"That user does not have any trophies.")
        else:
            trophy_string = f"🏆 " * user_data['trophies']
            self.send_privmsg(cmd.channel, f"{searchUser} has {user_data['trophies']} trophies in their collection. {trophy_string}")