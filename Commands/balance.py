from Utils.utils import check_cooldown, fetch_cmd_data, clean_str


def reply_with_balance(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    if cmd.params:
        searchUser = clean_str(cmd.params, ["@", ","])
        user_data = self.users.find_one({'user': searchUser.lower()})
        if not user_data:
            self.send_privmsg(cmd.channel, f"{cmd.username}, That user is not in the database.")
        else:
            self.send_privmsg(cmd.channel, f"{cmd.username}, {searchUser} has {user_data['points']} Pigga Coins.")

    else:
        user_data = self.users.find_one({'user': message['source']['nick']})
        if not user_data:
            self.send_privmsg(cmd.channel, f"{cmd.username}, you do not have any Pigga Coins. Use the daily command.")
        else:
            self.send_privmsg(cmd.channel, f"{cmd.username}, you have {user_data['points']} Pigga Coins.")