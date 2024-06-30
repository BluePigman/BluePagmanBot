import random
import time


def reply_with_roulette(self, message):
    if (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            self.cooldown):
        self.state[message['source']['nick']] = time.time()
        user_data = self.users.find_one({'user': message['source']['nick']})
        args = message['command']['botCommandParams'].split()
        if not user_data: 
            m = f"@{message['source']['nick']}, you do not have any Pigga Coins. Use the daily command."
            self.send_privmsg(message['command']['channel'], m)
        elif not message['command']['botCommandParams']:
            m = f"@{message['source']['nick']}, please enter a number or all."
            self.send_privmsg(message['command']['channel'], m)
            return
        else:
            user_points = user_data['points']
            amount = args[0]

            if user_points == 0:
                m = f"@{message['source']['nick']}, you don't have any Pigga Coins. PoroSad"
                self.send_privmsg(message['command']['channel'], m)
            else:
                if amount == 'all':
                    amount = user_points
                elif not amount.isdigit() or int(amount) <= 0:
                    m = f"@{message['source']['nick']}, please enter a positive number or 'all'."
                    self.send_privmsg(message['command']['channel'], m)
                    return  # Exit the function early if the input is invalid

                amount = int(amount)  # Convert the amount to an integer

                if amount > user_points:
                    m = f"@{message['source']['nick']}, you don't have enough Pigga Coins."
                    self.send_privmsg(message['command']['channel'], m)
                else:
                    gamba = random.randint(1, 2)
                    if gamba == 1:
                        self.users.update_one({'user': message['source']['nick']}, {'$inc': {'points': amount}})
                        new_balance = user_points + amount
                        m = f"@{message['source']['nick']}, you won {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins! Pog "
                        self.send_privmsg(message['command']['channel'], m)
                    else:
                        amountDec = -amount
                        self.users.update_one({'user': message['source']['nick']}, {'$inc': {'points': amountDec}})   
                        new_balance = user_points - amount
                        m =  f"@{message['source']['nick']}, you lost {amount} Pigga Coins in roulette and now have {new_balance} Pigga Coins! Saj"
                        self.send_privmsg(message['command']['channel'], m)
