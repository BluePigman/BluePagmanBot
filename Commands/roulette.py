import random
import time


def reply_with_roulette(self, message):
    if (message.user not in self.state or time.time() - self.state[message.user] >
            self.cooldown):
        self.state[message.user] = time.time()
        user_data = self.users.find_one({'user': message.user})

        if not user_data: 
            m = f"@{message.user}, you do not have any Pigga Coins. Use the daily command."
            self.send_privmsg(message.channel, m)
        elif not message.text_args:
            m = f"@{message.user}, please enter a number or all."
            self.send_privmsg(message.channel, m)
            return
        else:
            user_points = user_data['points']
            amount = message.text_args[0]

            if user_points == 0:
                m = f"@{message.user}, you don't have any Pigga Coins. PoroSad"
                self.send_privmsg(message.channel, m)
            else:
                if amount == 'all':
                    amount = user_points
                elif not amount.isdigit() or int(amount) <= 0:
                    m = f"@{message.user}, please enter a positive number or 'all'."
                    self.send_privmsg(message.channel, m)
                    return  # Exit the function early if the input is invalid

                amount = int(amount)  # Convert the amount to an integer

                if amount > user_points:
                    m = f"@{message.user}, you don't have enough Pigga Coins."
                    self.send_privmsg(message.channel, m)
                else:
                    gamba = random.randint(1, 2)
                    if gamba == 1:
                        self.users.update_one({'user': message.user}, {'$inc': {'points': amount}})
                        new_balance = user_points + amount
                        m = f'@{message.user}, you won {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins!'
                        self.send_privmsg(message.channel, m)
                    else:
                        amountDec = -amount
                        self.users.update_one({'user': message.user}, {'$inc': {'points': amountDec}})   
                        new_balance = user_points - amount
                        m =  f'@{message.user}, you lost {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins! Saj'
                        self.send_privmsg(message.channel, m)
