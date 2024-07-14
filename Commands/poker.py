import time, requests, config
from threading import Timer

from dankPoker import DankPokerGame

def reply_with_poker(self, message):
    if not (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
                self.cooldown):
        return
    
    self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        msg = "Play poker. Suffixes: start, join, fold, bet <amount>, call, or check. \
              The bot must be able to whisper you."
        self.send_privmsg(message['command']['channel'], msg)
        return

    if message['command']['botCommandParams'].lower() == "start" or message['command']['botCommandParams'].lower() == "play":
        if self.pokerGameActive:
            return
        if not tryWhisper(message['tags']['user-id']):
            self.send_privmsg(message['command']['channel'], "You have blocked whispers from strangers. \
                              Send a whisper to the bot to enable whispers temporarily and then try again. To send whispers \
                              you need to verify your phone number.")
            return
        
        self.send_privmsg(message['command']['channel'], f"A poker game has started. \
                          Type {self.command_prefix}poker join to join. Game starts in 30 seconds.")
        self.pokerGameActive = True
        self.pokerTimer = Timer(30, pokerTimeout, (self, message['command']['channel'],))
        self.pokerPlayers[message['tags']['display-name']] = message['tags']['user-id']
        self.pokerTimer.start()
        return

    elif message['command']['botCommandParams'].lower() == "join":
        if message['tags']['display-name'] in self.pokerPlayers or not self.pokerGameActive:
            return 

        # try whisper
        if not tryWhisper(message['tags']['user-id']):
            self.send_privmsg(message['command']['channel'], "You have blocked whispers from strangers. \
                              Send a whisper to the bot to enable whispers temporarily and then try again. To send whispers \
                              you need to verify your phone number.")
            return
        
        self.pokerPlayers[message['tags']['display-name']] = message['tags']['user-id']
        return
    
    elif message['command']['botCommandParams'].lower() == "fold":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            self.pokerGame.fold(message['tags']['display-name'])
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has folded for this round.")
            time.sleep(0.5)

    elif message['command']['botCommandParams'].lower().startswith("bet"):
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn() == message['tags']['display-name']:
            
            args = message['command']['botCommandParams'].split()
            if len(args) == 1:
                self.send_privmsg(message['command']['channel'], "Invalid bet. Must be a positive integer.")
                time.sleep(0.5)
                return
            amount = args[1]
            if amount.isdigit() and int(amount) > 0:
                if not self.pokerGame.bet(message['tags']['display-name'], int(amount)):
                    self.send_privmsg(message['command']['channel'], f"You don't have that many chips. Use {self.command_prefix}poker chips to see your chips.")
                    time.sleep(0.5)
                    return
                if int(amount) < self.pokerGame.currentMaxBet:
                    self.send_privmsg(message['command']['channel'], "Your bet must be at least the current max bet, " + str(self.pokerGame.currentMaxBet))
                    time.sleep(0.5)
                    return 
                self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has bet {amount}. The pot is now {self.pokerGame.pot}.")
                time.sleep(0.5)

            else:
                self.send_privmsg(message['command']['channel'], "Invalid bet. Must be a positive integer.")
                time.sleep(1)
                self.send_privmsg(message['command']['channel'], f"Your turn, {self.pokerGame.get_turn()}")

    elif message['command']['botCommandParams'].lower() == "pot":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            self.send_privmsg(message['command']['channel'], f"The current pot is {self.pokerGame.pot}.")
            time.sleep(0.5)
        return

    elif message['command']['botCommandParams'].lower() == "chips":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            self.send_privmsg(message['command']['channel'], f"You have {self.pokerGame.get_chips(message['tags']['display-name'])} chips.")
            time.sleep(0.5)
        return
    
    elif message['command']['botCommandParams'].lower() == "call":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn()  == message['tags']['display-name']:
            self.pokerGame.call(message['tags']['display-name'])
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has called. The pot is now {self.pokerGame.pot}.")
            time.sleep(0.5)
    
    elif message['command']['botCommandParams'].lower() == "check":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn()  == message['tags']['display-name']:
            self.pokerGame.check(message['tags']['display-name'])
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has checked.")
            time.sleep(0.5)

    elif message['command']['botCommandParams'].lower() == "chips":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has {self.pokerGame.get_chips([message['tags']['display-name']])} chips.")
            time.sleep(0.5)
        return
    
    if self.pokerGameActive and self.pokerGame.is_betting_round_complete():
        if self.pokerGame.phase == "flop":
            self.send_privmsg(message['command']['channel'], "Everyone has bet. The pot is now " + str(self.pokerGame.pot) + ".")
            time.sleep(1)
            self.pokerGame.phase = "turn"
            self.pokerGame.deal_turn()
            self.send_privmsg(message['command']['channel'], f"Cards dealt. The board is {self.pokerGame.pretty_print_emojis(self.pokerGame.board)}.")
        elif self.pokerGame.phase == "turn":
            self.send_privmsg(message['command']['channel'], "Everyone has bet. The pot is now " + str(self.pokerGame.pot) + ".")
            time.sleep(1)
            self.pokerGame.phase = "river"
            self.pokerGame.deal_river()
            self.send_privmsg(message['command']['channel'], f"Cards dealt. The board is {self.pokerGame.pretty_print_emojis(self.pokerGame.board)}.")
        elif self.pokerGame.phase == "river":
            # determine winner.
            winner, hand_name = self.pokerGame.get_winner()
            self.send_privmsg(message['command']['channel'], f"The winner is {winner}, with a {hand_name}.")
            self.pokerGame.distribute_chips()
            time.sleep(1)
            self.send_privmsg(message['command']['channel'], "game over ok")
            self.pokerGameActive = False
            

    else:
        if self.pokerGameActive:
            self.send_privmsg(message['command']['channel'], f"Your turn, {self.pokerGame.get_turn()} Usage: {self.command_prefix} poker  fold, bet <amount>, call, or check.")


def pokerTimeout(self, channel):
    if len(self.pokerPlayers) == 1:
        text = "No one accepted the challenge. :("
        self.send_privmsg(channel, text)
        self.pokerGameActive = False
        self.pokerPlayers = {}
        return
    msg = "Poker is starting, joined users: " + ", ".join(self.pokerPlayers)
    self.send_privmsg(channel, msg)
    time.sleep(0.5)
    runPokerRound(self, channel)
    

def runPokerRound(self, channel):
    
    self.pokerGame = DankPokerGame(self.pokerPlayers)
    self.pokerGame.deal_to_all_players()
    for player in self.pokerPlayers:
        if not whisperCards(self, self.pokerPlayers[player], player):
            self.send_privmsg(channel, f"Error, unable to whisper {player}'s poker cards. The game will end.")
            self.endPokerGame()
            return
        time.sleep(0.75)
    
    self.pokerGame.deal_flop()

    self.send_privmsg(channel, f"Cards dealt. The board is {self.pokerGame.pretty_print_emojis(self.pokerGame.board)}.")
    time.sleep(0.5)

    self.send_privmsg(channel, f"Your turn, {self.pokerGame.get_turn()}. Use {self.command_prefix}poker fold, bet <amount>, call, or check")

    # The flop

    # players now must make bets. First player can either bet or fold. 
    # while loop stopping condition : either everyone folded or All players have bet the currentMaxBet 
    # or only 1 player remains as everyone else folded.
    # If player folds, next player can make a bet or fold.
    # as soon as a bet is made, others can raise or fold.
    # if one raises, then the people that have bet originally must call or fold.
    # if a player does not have enough to call, they can either all in or fold.
    # Players that fold should set their attribute to true, then skip them in the current round. 
    # The turn

    # The river

    # Determine winner: all players that have not folded, compare their hands. 

def endPokerGame(self):
    self.pokerGameActive = False
    self.pokerPlayers = {}
    self.pokerGame = None

headers = {
            'Authorization': f"Bearer {config.user_access_token}",
            'Client-ID': f'{config.client_id}',
        }



def tryWhisper(user_id):
    params = {
    'from_user_id': config.user_id,
    'to_user_id': user_id
    }
    body = {
    'message': 'The bot will send you a whisper for your cards.',
    }
    response = requests.post('https://api.twitch.tv/helix/whispers', headers=headers, params=params, json=body)
    if response.status_code == 204:
        return True
    if response.status_code == 401:
        return False
    
def whisperCards(self, user_id, username):
    cards = self.pokerGame.players[username]['hand']
    cards = self.pokerGame.pretty_print_emojis(cards)
    params = {
    'from_user_id': config.user_id,
    'to_user_id': user_id
    }
    body = {
    'message': f"Your cards for this round are {cards}"
    }
    response = requests.post('https://api.twitch.tv/helix/whispers', headers=headers, params=params, json=body)
    if response.status_code == 204:
        return True
    if response.status_code == 401:
        return False