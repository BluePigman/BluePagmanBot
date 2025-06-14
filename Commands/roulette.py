import random
from Utils.utils import check_cooldown, fetch_cmd_data


def reply_with_roulette(self, message):
    cmd = fetch_cmd_data(self, message)
    if not check_cooldown(cmd.state, cmd.nick, cmd.cooldown): 
        return

    user_data = self.users.find_one({'user': cmd.nick})
    if not user_data:
        self.send_privmsg(cmd.channel, f"{cmd.username}, you do not have any Pigga Coins. Use the daily command.")
        return

    if not cmd.params:
        self.send_privmsg(cmd.channel, f"{cmd.username}, please enter a number or all")
        return

    user_points = user_data['points']
    if user_points == 0:
        self.send_privmsg(cmd.channel, f"{cmd.username}, you don't have any Pigga Coins. PoroSad")
        return

    amount = cmd.params.split()[0]
    if amount == 'all':
        amount = user_points
    elif not amount.isdigit() or int(amount) <= 0:
        self.send_privmsg(cmd.channel, f"{cmd.username}, please enter a positive number or all")
        return
    else:
        amount = int(amount)

    if amount > user_points:
        self.send_privmsg(cmd.channel, f"{cmd.username}, you don't have enough Pigga Coins.")
        return

    gamba = random.randint(1, 2)
    if gamba == 1:
        self.users.update_one({'user': cmd.nick}, {'$inc': {'points': amount}})
        new_balance = user_points + amount
        self.send_privmsg(cmd.channel, f"{cmd.username}, you won {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins! Pog ")
    else:
        self.users.update_one({'user': cmd.nick}, {'$inc': {'points': -amount}})
        new_balance = user_points - amount
        self.send_privmsg(cmd.channel, f"{cmd.username}, you lost {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins! Saj")