import time
import requests
import config
from threading import Timer
from Classes.dankPoker import DankPokerGame


def reply_with_poker(self, message):
    if not (message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] >
            1):
        return
    self.state[message['source']['nick']] = time.time()

    if not message['command']['botCommandParams']:
        msg = "Play poker. Suffixes: start, join, fold, bet <amount>, call, or check. \
              The bot must be able to whisper you."
        self.send_privmsg(message['command']['channel'], msg)
        return

    if self.pokerGameActive and message['tags']['display-name'] not in self.pokerPlayers:
        return

    if message['command']['botCommandParams'].lower() == "start" or message['command']['botCommandParams'].lower() == "play":
        if self.pokerGamePending:
            return
        if not tryWhisper(message['tags']['user-id']):
            self.send_privmsg(message['command']['channel'], "You have blocked whispers from strangers. \
                              Send a whisper to the bot to enable whispers temporarily and then try again. To send whispers \
                              you need to verify your phone number.")
            return

        self.send_privmsg(message['command']['channel'], f"A poker game has started. \
                          Type {self.prefix}poker join to join. Game starts in 30 seconds.")
        self.pokerGamePending = True
        self.pokerTimer = Timer(
            30, pokerTimeout, (self, message['command']['channel'],))
        self.pokerPlayers[message['tags']['display-name']
                          ] = message['tags']['user-id']
        self.pokerTimer.start()
        return

    elif message['command']['botCommandParams'].lower() == "join":
        if message['tags']['display-name'] in self.pokerPlayers or not self.pokerGamePending:
            return

        # try whisper
        if not tryWhisper(message['tags']['user-id']):
            self.send_privmsg(message['command']['channel'], "You have blocked whispers from strangers. \
                              Send a whisper to the bot to enable whispers temporarily and then try again. To send whispers \
                              you need to verify your phone number.")
            return

        self.pokerPlayers[message['tags']['display-name']
                          ] = message['tags']['user-id']
        return

    elif message['command']['botCommandParams'].lower() == "fold":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            x = self.pokerGame.fold(message['tags']['display-name'])
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has folded for this round.")
            if x:
                self.send_privmsg(message['command']
                                  ['channel'], f"{x} wins the pot.")
                time.sleep(1)
                verifyPlayers(self)
                self.pokerGame.start_new_round()
            time.sleep(0.5)

    elif message['command']['botCommandParams'].lower().startswith("bet"):
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn() == message['tags']['display-name']:

            args = message['command']['botCommandParams'].split()
            if len(args) == 1:
                self.send_privmsg(
                    message['command']['channel'], "Invalid bet. Must be a positive integer.")
                time.sleep(0.5)
                return
            amount = args[1]
            if amount.isdigit() and int(amount) > 0:
                if not self.pokerGame.bet(message['tags']['display-name'], int(amount)):
                    self.send_privmsg(message['command']['channel'], f"You don't have that many chips. Use {self.prefix}poker chips to see your chips.")
                    time.sleep(0.5)
                    return
                if int(amount) < self.pokerGame.currentMaxBet:
                    self.send_privmsg(
                        message['command']['channel'], "Your bet must be at least the current max bet, " + str(self.pokerGame.currentMaxBet))
                    time.sleep(0.5)
                    return
                self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has bet {amount}. The pot is now {self.pokerGame.pot}.")
                time.sleep(0.5)

            else:
                self.send_privmsg(
                    message['command']['channel'], "Invalid bet. Must be a positive integer.")
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
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn() == message['tags']['display-name']:
            self.pokerGame.call(message['tags']['display-name'])
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has called. The pot is now {self.pokerGame.pot}.")
            time.sleep(0.5)

    elif message['command']['botCommandParams'].lower() == "check":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers and self.pokerGame.get_turn() == message['tags']['display-name']:
            if not self.pokerGame.check(message['tags']['display-name']):
                self.send_privmsg(
                    message['command']['channel'], "You cannot check, you must bet, fold or raise. The current max bet is " + str(self.pokerGame.currentMaxBet))
                return
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has checked.")
            time.sleep(0.5)

    elif message['command']['botCommandParams'].lower() == "chips":
        if self.pokerGameActive and message['tags']['display-name'] in self.pokerPlayers:
            self.send_privmsg(message['command']['channel'], f"{message['tags']['display-name']} has {self.pokerGame.get_chips([message['tags']['display-name']])} chips.")
            time.sleep(1)
        return

    if self.pokerGameActive and self.pokerGame.is_betting_round_complete():
        if self.pokerGame.phase == "flop":
            self.send_privmsg(
                message['command']['channel'], "Everyone has bet. The pot is now " + str(self.pokerGame.pot) + ".")
            time.sleep(1)
            self.pokerGame.phase = "turn"
            self.pokerGame.deal_turn()
            self.send_privmsg(message['command']['channel'], f"Cards dealt. The board is {self.pokerGame.pretty_print_emojis(self.pokerGame.board)}.")
        elif self.pokerGame.phase == "turn":
            self.send_privmsg(
                message['command']['channel'], "Everyone has bet. The pot is now " + str(self.pokerGame.pot) + ".")
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
            if self.pokerGame.round == 5:
                self.send_privmsg(message['command']
                                  ['channel'], "game over ok")
                self.pokerGameActive = False
                endPokerGame(self)
                return
            else:
                printChips(self, message['command']['channel'])
                time.sleep(1)
                verifyPlayers(self)
                self.pokerGame.start_new_round()
                self.send_privmsg(
                    message['command']['channel'], "Next round starting...")
                time.sleep(1)
                runPokerRound(self, message['command']
                              ['channel'], self.pokerGame.round)

    else:
        if self.pokerGameActive:
            self.send_privmsg(message['command']['channel'], f"Your turn, {self.pokerGame.get_turn()} Usage: {self.prefix}poker  fold, bet <amount>, call, or check.")


def pokerTimeout(self, channel):
    if len(self.pokerPlayers) == 1:
        text = "No one accepted the challenge. :("
        self.send_privmsg(channel, text)
        self.pokerGamePending = False
        self.pokerPlayers = {}
        return
    msg = "Poker is starting, joined users: " + ", ".join(self.pokerPlayers)
    self.pokerGameActive = True
    self.send_privmsg(channel, msg)
    time.sleep(0.5)
    runPokerRound(self, channel, 0)


def printChips(self, channel):
    msg = ""
    for player in self.pokerPlayers:
        msg += f"{player}: {self.pokerGame.get_chips(player)} chips. "
    self.send_privmsg(channel, msg)


def verifyPlayers(self):
    for player in self.pokerPlayers:
        if player not in self.pokerGame.players:
            self.pokerPlayers.pop(player)
    return


def runPokerRound(self, channel, round):
    if round == 0:
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

    self.send_privmsg(channel, f"Your turn, {self.pokerGame.get_turn()}. Use {self.prefix}poker fold, bet <amount>, call, or check")

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
    response = requests.post(
        'https://api.twitch.tv/helix/whispers', headers=headers, params=params, json=body)
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
    response = requests.post(
        'https://api.twitch.tv/helix/whispers', headers=headers, params=params, json=body)
    if response.status_code == 204:
        return True
    if response.status_code == 401:
        return False
