"""
This is a chat bot for Twitch with some basic commands, and allows you
to play a game of chess against another chatter.
@Bluepigman5000

"""

import socket
import sys
import ssl
import datetime
from collections import namedtuple
import time
import random
import config
import chess
import chessCommands
from threading import Timer

Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args',
)


def remove_prefix(string, prefix):
    if not string.startswith(prefix):
        return string
    return string[len(prefix):]


class Bot:

    def __init__(self):
        # Parameters
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6697
        self.oauth_token = config.OAUTH_TOKEN
        self.username = config.username
        self.channels = config.channels
        self.command_prefix = config.prefix
        self.state = {}  # dictionary for cooldown
        self.cooldown = 5  # default cooldown for commands
        self.joke = random.randint(0, 84)
        self.time = time.time()
        self.last_msg = ''
        self.last_msg_time = time.time()
        # chess params
        self.chessGameActive = False
        self.gameAccepted = False
        self.player1 = ''
        self.player2 = ''
        self.choseSidePlayer1 = False
        self.currentGame = None  # hold the chess game
        self.chessTimer = None  # chess game pending timer
        # anyone can use these
        self.custom_commands = {
            'date': self.reply_with_date,
            'ping': self.reply_to_ping,
            'help': self.list_commands,
            'help_chess': self.reply_with_chesshelp,
            'source_code': self.reply_with_source_code,
            'play_chess': self.play_chess,
            'bot': self.reply_with_bot,
            'ro': self.reply_with_random_opening,
            'joke': self.reply_with_joke,
            'r960': self.reply_with_random960,
            'help_ro': self.reply_with_help_ro,
            'pyramid': self.reply_with_pyramid,
            'slow_pyramid': self.reply_with_slow_pyramid
        }

        # only bot owner can use these commands
        self.private_commands = {
            'leave': self.leave,
            'say': self.say,
            'echo': self.echo,
            'join_channel': self.join_channel,
            'leave_channel': self.part_channel,
            'reset_chess': self.reset_chess
        }

        # commands for playing chess
        self.chess_commands = {
            'white': self.chooseSidePlayer1,
            'black': self.chooseSidePlayer1,
            'move': self.move,
            'join': self.join
        }

    def send_privmsg(self, channel, text):
        if text == self.last_msg and (time.time() - self.last_msg_time) < 30:
            text += ' \U000e0000'
            self.send_command(f'PRIVMSG #{channel} : {text}')
            self.last_msg_time = time.time()
            self.last_msg = text
        else:
            self.send_command(f'PRIVMSG #{channel} : {text}')
            self.last_msg_time = time.time()
            self.last_msg = text

    def send_command(self, command):
        if 'PASS' not in command:
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode())

    def connect(self):
        self.irc = ssl.create_default_context().wrap_socket(
            socket.socket(), server_hostname=self.irc_server)
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, 'forsenEnter')
        self.loop_for_messages()

    def get_user_from_prefix(self, prefix):
        domain = prefix.split('!')[0]
        if domain.endswith('.tmi.twitch.tv'):
            return domain.replace('.tmi.twitch.tv', '')
        if 'tmi.twitch.tv' not in domain:
            return domain
        return None

    def parse_message(self, received_msg):
        parts = received_msg.split(' ')

        prefix = None
        user = None
        channel = None
        text = None
        text_command = None
        text_args = None
        irc_command = None
        irc_args = None

        if parts[0].startswith(':'):
            prefix = remove_prefix(parts[0], ':')
            user = self.get_user_from_prefix(prefix)
            parts = parts[1:]

        text_start = next(
            (idx for idx, part in enumerate(parts) if part.startswith(':')),
            None
        )
        if text_start is not None:
            text_parts = parts[text_start:]
            text_parts[0] = text_parts[0][1:]
            text = ' '.join(text_parts)
            if text_parts[0].startswith(self.command_prefix):
                text_command = remove_prefix(
                    text_parts[0], self.command_prefix)
                text_args = text_parts[1:]
            parts = parts[:text_start]

        irc_command = parts[0]
        irc_args = parts[1:]

        hash_start = next(
            (idx for idx, part in enumerate(irc_args) if part.startswith('#')),
            None
        )
        if hash_start is not None:
            channel = irc_args[hash_start][1:]

        message = Message(
            prefix=prefix,
            user=user,
            channel=channel,
            text=text,
            text_command=text_command,
            text_args=text_args,
            irc_command=irc_command,
            irc_args=irc_args,
        )

        return message

    def handle_message(self, received_msg):
        if len(received_msg) == 0:
            return

        message = self.parse_message(received_msg)
        # can uncomment these for information on every message
        print(f'> {message}')
        print(f'> {received_msg}')

        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        # If message starts with the prefix, follows 1s cooldown
        if message.irc_command == 'PRIVMSG' and \
                message.text.startswith(self.command_prefix) \
                and time.time() - self.time > 1:

            if message.text_command.lower() in self.custom_commands:
                self.custom_commands[message.text_command.lower()](message)
                self.time = time.time()

            if message.text_command.lower() in self.private_commands:
                self.private_commands[message.text_command.lower()](message)
                self.time = time.time()

            if message.text_command.lower() in self.chess_commands:
                self.chess_commands[message.text_command.lower()](message)
                self.time = time.time()

            # Aliases.
            if message.text_command.lower() == "commands":
                self.custom_commands["help"](message)
                self.time = time.time()

    def loop_for_messages(self):
        while True:
            received_msgs = self.irc.recv(4096).decode(errors='ignore')
            for received_msg in received_msgs.split('\r\n'):
                self.handle_message(received_msg)

    """ General Commands here"""

    def reply_with_date(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            text = f'{message.user}, the date is {formatted_date} EST.'
            self.send_privmsg(message.channel, text)

    def reply_to_ping(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            text = f'@{message.user}, forsenEnter'
            self.send_privmsg(message.channel, text)

    def reply_with_source_code(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            text = 'Source code: https://github.com/BluePigman/BluePagmanBot'
            self.send_privmsg(message.channel, text)

    def list_commands(self, message):
        custom_cmd_names = list(self.custom_commands.keys())
        all_cmd_names = [
            self.command_prefix + cmd
            for cmd in custom_cmd_names
        ]
        text = "" f'@{message.user}, Commands: ' + ' '.join(all_cmd_names)
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            self.send_privmsg(message.channel, text)

    def reply_with_bot(self, message):

        text = 'BluePAGMANBot is a bot made by @Bluepigman5000 in Python. \
        It has some basic commands, and can run a game of chess in chat \
        between two different players.'

        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            self.send_privmsg(message.channel, text)

    def reply_with_random_opening(self, message):

        text = f'@{message.user}, '

        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()

            # if args present
            if (message.text_args):

                if '-w' in message.text_args:
                    # get opening for white
                    side = 'w'
                    message.text_args.remove('-w')
                    name = " ".join(message.text_args)
                    if '\U000e0000' in name:
                        name = name.replace('\U000e0000', '')

                    opening = chessCommands.getRandomOpeningSpecific(
                        name, side)
                    self.send_privmsg(message.channel, text + opening)

                elif '-b' in message.text_args:
                    # get opening for black
                    side = 'b'
                    message.text_args.remove('-b')
                    name = " ".join(message.text_args)
                    if '\U000e0000' in name:
                        name = name.replace('\U000e0000', '')

                    opening = chessCommands.getRandomOpeningSpecific(
                        name, side)
                    self.send_privmsg(message.channel, text + opening)

                else:  # get opening for specified search term
                    name = " ".join(message.text_args)
                    if '\U000e0000' in name:
                        name = name.replace('\U000e0000', '')

                    opening = chessCommands.getRandomOpeningSpecific(name)
                    self.send_privmsg(message.channel, text + opening)

            else:  # No arguments
                opening = chessCommands.getRandomOpening()
                self.send_privmsg(message.channel, text + opening)

    def reply_with_random960(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            opening = chessCommands.getRandom960()
            self.send_privmsg(message.channel, opening)

    def reply_with_joke(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            setup, punchline = chessCommands.getJoke(self.joke)
            self.send_privmsg(message.channel, setup)
            punchline = punchline.strip('\n')
            x = random.randint(0, 10)
            if x > 1:
                response = f'{punchline} haHAA'
            else:
                response = f'{punchline} Pepepains'
            time.sleep(3)
            self.send_privmsg(message.channel, response)
            self.joke += 1
            if self.joke > 84:
                self.joke = 0

    # https://stackoverflow.com/q/6266727
    def reply_with_pyramid(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            if len(message.text_args) > 1 and message.text_args[1].isnumeric():
                emote = message.text_args[0]
                width = int(message.text_args[1])
                if len(emote) * width + width - 1 < 500:
                    text = ''
                    for x in range(width):  # go up
                        text += (emote + ' ')
                        self.send_privmsg(message.channel, text)
                        time.sleep(0.1)
                    for y in range(width):  # go down
                        text = text.rsplit(emote, 1)[0]
                        self.send_privmsg(message.channel, text)
                        time.sleep(0.1)
                else:
                    text = 'Pyramid is too large to be displayed in chat. Use \
                    a smaller pyramid width.'
                    self.send_privmsg(message.channel, text)

            else:
                text = f'Width must be an integer. Usage: {self.command_prefix}pyramid {{name}} {{width}}'
                self.send_privmsg(message.channel, text)

    def reply_with_slow_pyramid(self, message):
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            if len(message.text_args) > 1 and message.text_args[1].isnumeric():
                emote = message.text_args[0]
                width = int(message.text_args[1])
                if len(emote) * width + width - 1 < 500:
                    text = ''
                    for x in range(width):  # go up
                        text += (emote + ' ')
                        self.send_privmsg(message.channel, text)
                        time.sleep(1.6)
                    for y in range(width):  # go down
                        text = text.rsplit(emote, 1)[0]
                        self.send_privmsg(message.channel, text)
                        time.sleep(1.6)
                else:
                    text = 'Pyramid is too large to be displayed in chat. Use \
                    a smaller pyramid width.'
                    self.send_privmsg(message.channel, text)

            else:
                text = f'Width must be an integer. Usage: {self.command_prefix}pyramid {{name}} {{width}}'
                self.send_privmsg(message.channel, text)

    """ Chess commands """

    def reply_with_chesshelp(self, message):
        text = (f'@{message.user}, to make a move, type the square of the \
            piece you want to move followed by the square you want to go to, \
            same applies for captures. For example, if you want to move the  \
            pawn from e2 to e4, you type {self.command_prefix}move e2e4. Input must be in \
            lowercase.')
        text2 = f'For promotions, add the letter \
        of the piece you would like to promote to at the end \
        (e.g. {self.command_prefix}move g7h8q). To resign type {self.command_prefix}move resign.'

        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            self.send_privmsg(message.channel, text)
            time.sleep(2)
            self.send_privmsg(message.channel, text2)

    def reply_with_help_ro(self, message):
        text = (f"@{message.user}, Gets a random opening. You can add -b or -w \
for a specific side, and/or add a name for search. e.g. {self.command_prefix}ro King's Indian \
                Defense -w")
        if (message.user not in self.state or time.time() - self.state[message.user] >
                self.cooldown):
            self.state[message.user] = time.time()
            self.send_privmsg(message.channel, text)

    """Private commands"""

    def leave(self, message):
        text = 'forsenLeave'
        if message.user == config.bot_owner:
            self.send_privmsg(message.channel, text)
            sys.exit()
        else:
            if ("leave" not in self.state or time.time() - self.state["leave"] >
                    self.cooldown):
                self.state["leave"] = time.time()
                self.send_privmsg(message.channel, "NOIDONTTHINKSO")

    def say(self, message):
        if message.user == config.bot_owner:
            self.send_privmsg(message.channel, " ".join(message.text_args))

    # Use: #echo CHANNEL text, will send message text in specified channel.
    def echo(self, message):
        if len(message.text_args) > 1:
            channel = " ".join(message.text_args[0:1])
            text = " ".join(message.text_args[1:])
            if message.user == config.bot_owner:
                self.send_privmsg(channel, text)

    # Work in progress.
    def join_channel(self, message):
        if message.user == config.bot_owner:
            newChannel = " ".join(message.text_args[0:1])
            self.send_command(f'JOIN #{newChannel}')
            self.send_privmsg(newChannel, "forsenEnter")
            self.send_privmsg(message.channel, "Success")

    def part_channel(self, message):
        if message.user == config.bot_owner:
            newChannel = " ".join(message.text_args[0:1])
            self.send_privmsg(newChannel, "forsenLeave")
            self.send_command(f'PART #{newChannel}')

            self.send_privmsg(message.channel, "Success")

    def reset_chess(self, message):
        if message.user == self.player1 or message.user == self.player2:
            self.chessGameActive = False
            self.gameAccepted = False
            # self.send_privmsg(message.channel, "Chess game has been ended.")
            self.player1 = ""
            self.player2 = ""
            self.chessGameActive = False
            self.choseSidePlayer1 = False
            self.currentGame = None
            time.sleep(2)

    # Runs if no one accepts chess challenge after 30s.
    def gameTimeout(self, channel):
        text = "No one accepted the challenge. :("
        self.send_privmsg(channel, text)
        self.chessGameActive = False
        self.player1 = ""

    """Functions for chess"""

    def join(self, message):  # join game
        if message.user != self.player1 and self.chessGameActive and not self.gameAccepted:
            self.chessTimer.cancel()
            text = f'@{message.user} has joined the game.'
            self.send_privmsg(message.channel, text)
            time.sleep(2)
            # side
            self.player2 = message.user
            self.gameAccepted = True
            text = f"@{self.player1}, Choose a side: {self.command_prefix}white (white), {self.command_prefix}black (black)"
            self.send_privmsg(message.channel, text)
            time.sleep(2)
        pass

    def play_chess(self, message):  # start a game of chess

        if not self.chessGameActive:
            self.chessGameActive = True
            self.player1 = message.user
            text = f'@{self.player1} has started a chess game. Type {self.command_prefix}join to join \
                the game.'
            self.send_privmsg(message.channel, text)
            self.chessTimer = Timer(30, self.gameTimeout, (message.channel,))
            self.chessTimer.start()  # start a timer of 30s.

    def chooseSidePlayer1(self, message):
        # Player who started game chooses side first.
        if self.chessGameActive and self.player2 and message.user == self.player1 and not self.choseSidePlayer1:

            if message.text_command.lower() == "white":
                self.choseSidePlayer1 = True
                text = f"@{self.player1}, you will play as white"
                self.send_privmsg(message.channel, text)
                time.sleep(2)
                text = f"@{self.player1}, you are starting, enter start move."
                self.send_privmsg(message.channel, text)
                # instantiate new chess game
                self.currentGame = chessGame(self.player1, self.player2)
                time.sleep(2)

            elif message.text_command.lower() == "black":
                text = f"@{self.player1}, you will play as black"
                self.send_privmsg(message.channel, text)
                time.sleep(2)
                text = f"@{self.player2}, you are starting, enter start move."
                self.send_privmsg(message.channel, text)
                self.currentGame = chessGame(self.player2, self.player1)
                time.sleep(2)
            else:
                text = f"Invalid input, please enter \
                either {self.command_prefix}white or {self.command_prefix}black."
                self.send_privmsg(message.channel, text)
                time.sleep(2)

    # Start the game

    def move(self, message):
        if self.currentGame and \
           ("move" not in self.state or time.time() - self.state["move"] > 2):

            self.state["move"] = time.time()

            # White to play
            if self.currentGame.currentSide == 'w':
                # print('white: ', self.currentGame.player1)

                if message.user == self.currentGame.player1:
                    if not message.text_args:
                        self.send_privmsg(
                            message.channel, f'@{self.currentGame.player1}, please enter a move!')
                    else:
                        move = message.text_args[0]
                        if move == "resign":
                            self.currentGame.resign(
                                message.user)  # will update pgn
                            text = f"@{message.user} resigned. @{self.currentGame.player2} wins."
                            self.send_privmsg(message.channel, text)
                            time.sleep(2)
                            # get pgn
                            pgn = self.currentGame.getPGN()
                            for m in pgn:
                                self.send_privmsg(message.channel, m)
                                time.sleep(2)
                            # reset chess vars.
                            self.chessGameActive = False
                            self.gameAccepted = False
                            self.choseSidePlayer1 = False
                            self.currentGame = None
                            self.player1 = ""
                            self.player2 = ""
                            return
                        moveSuccesful = self.currentGame.move(move)
                        # do the move
                        if moveSuccesful:
                            if self.currentGame.gameOver():
                                result = self.currentGame.result()
                                self.send_privmsg(message.channel, result)
                                time.sleep(2)
                                for m in self.currentGame.getPGN():  # print PGN
                                    self.send_privmsg(message.channel, m)
                                    time.sleep(2)
                                self.chessGameActive = False
                                self.choseSidePlayer1 = False
                                self.gameAccepted = False
                                self.currentGame = None
                                self.player1 = ""
                                self.player2 = ""
                                return
                            # if game not over, print PGN, black to play.
                            for m in self.currentGame.getPGN():
                                self.send_privmsg(message.channel, m)
                                time.sleep(2)
                            self.send_privmsg(
                                message.channel, f"@{self.currentGame.player2} it is your turn.")

                        else:  # move was unsuccessful
                            text = f"Invalid/illegal move, please try again. \
                            For help refer to {self.command_prefix}help_chess."
                            self.send_privmsg(message.channel, text)
                            time.sleep(2)

            elif self.currentGame.currentSide == 'b':

                if message.user == self.currentGame.player2:
                    if not message.text_args:
                        self.send_privmsg(
                            message.channel, f'@{self.currentGame.player2}, please enter a move!')
                    else:
                        move = message.text_args[0]
                        if move == "resign":
                            self.currentGame.resign(
                                message.user)  # will update pgn
                            text = f"@{message.user} resigned. @{self.currentGame.player1} wins! PogChamp"
                            self.send_privmsg(message.channel, text)
                            time.sleep(2)
                            # get pgn
                            pgn = self.currentGame.getPGN()
                            for m in pgn:
                                self.send_privmsg(message.channel, m)
                                time.sleep(2)
                            # reset chess vars.
                            self.chessGameActive = False
                            self.choseSidePlayer1 = False
                            self.gameAccepted = False
                            self.currentGame = None
                            self.player1 = ""
                            self.player2 = ""
                            return
                        moveSuccesful = self.currentGame.move(move)
                        # do the move
                        if moveSuccesful:
                            if self.currentGame.gameOver():
                                result = self.currentGame.result()
                                self.send_privmsg(message.channel, result)
                                for m in self.currentGame.getPGN():  # print PGN
                                    self.send_privmsg(message.channel, m)
                                    time.sleep(2)
                                # reset chess vars.
                                self.chessGameActive = False
                                self.gameAccepted = False
                                self.choseSidePlayer1 = False
                                self.currentGame = None
                                self.player1 = ""
                                self.player2 = ""
                                return
                            # if game not over, print PGN, white to play.
                            for m in self.currentGame.getPGN():
                                self.send_privmsg(message.channel, m)
                                time.sleep(2)
                            self.send_privmsg(
                                message.channel, f"@{self.currentGame.player1} it is your turn.")

                        else:  # move was unsuccessful
                            text = f"Invalid/illegal move, please try again. \
                            For help refer to {self.command_prefix}help_chess."
                            self.send_privmsg(message.channel, text)
                            time.sleep(2)


class chessGame:
    def __init__(self, player1, player2):
        # params

        self.board = chess.Board()
        # self.board.reset()
        self.player1 = player1  # player 1 is white, player 2 is black
        self.player2 = player2
        self.pgn = ""
        self.currentSide = "w"
        self.moveCount = 0
        self.increment = 0
        self.userQuit = False

    def getLegalMoves(self):
        return list(self.board.legal_moves)

    def isLegalMove(self, move):
        return move in list(self.board.legal_moves)

    def switchSide(self):
        if self.currentSide == "w":
            self.currentSide = "b"
            return
        self.currentSide = "w"

    def move(self, move: str):
        """ Make the move on the chess board.
        First convert the SAN move (e.g. "e4") into UCI (e2e4)
        Then use this UCI to convert back to SAN, in order to 
        add symbols representing check or checkmate, if they were missing.
        return True if move was success, False otherwise.
        """

        if '\U000e0000' in move:
            move = move.replace('\U000e0000', '')

        try:
            uci = self.board.parse_san(move)  # convert SAN to UCI

            if self.increment % 2 == 0:
                self.moveCount += 1
                self.pgn += str(self.moveCount) + ". " +  \
                    self.get_san(uci) + " "
            else:
                self.pgn += self.get_san(uci) + " "
            self.board.push_san(move)
            self.increment += 1
            self.switchSide()
            return True
        except:
            return False

    def getPGN(self):
        return self.split_pgn()

    def resign(self, player):  # player resigns
        if player == self.player1:
            self.pgn = self.pgn + "{ White resigns. } 0-1"
        else:
            self.pgn = self.pgn + " { Black resigns. } 1-0"

    def reset(self):
        self.player1 = ""
        self.player2 = ""
        self.board.reset()
        self.pgn = ""

        self.currentSide = "w"

        self.moveCount = 0

        self.increment = 0

    def updatePGN(self, move):
        pass

    def gameOver(self):
        # Check if the game is over (by checkmate, stalemate,
        # draw by insufficient material, or draw by fivefold repetition)
        return self.board.is_checkmate() or self.board.is_stalemate() or \
            self.board.is_insufficient_material() or self.board.is_fivefold_repetition()

    # Return the result of the game in a string. (Player1 wins/Player2 wins/
    # stalemate/draw by insufficient material

    def result(self):
        if self.board.is_checkmate():
            result = str(self.board.outcome())
            winner = result[55:]

            if winner[:len(winner) - 1] == "True":  # White wins.
                self.pgn += ' { White wins by checkmate. } 1-0'
                result = (f"Checkmate, {self.player1} wins! PogChamp")
                return result

            else:  # Black wins
                self.pgn += ' { Black wins by checkmate. } 0-1'

                result = (f"Checkmate, {self.player2} wins! PogChamp")
                return result

        elif self.board.is_stalemate():  # Check for stalemate
            self.pgn += ' { Draw by stalemate. } 1/2-1/2'
            result = "Stalemate LUL"
            return result

        elif self.board.is_insufficient_material():  # Check for draw by insufficient material
            pgn += ' { The game is a draw. } 1/2-1/2'
            result = "Draw by insufficient material."
            return result

        else:  # Fivefold repetition
            pgn += ' { The game is a draw. } 1/2-1/2'
            result = "Draw by fivefold repetition."
            return result

    """
    Get standard algebraic notation of move (e2e4 becomes e4).
    move is a uci representation of move.
    """

    def get_san(self, move):
        return self.board.san(move)

    # Split the long message into a list of under 500 character messages.
    # pgn is a string

    def split_pgn(self):
        n = 500
        """ Get substrings from i to specified length n, put into list.
        For loop from 0 to length of pgn, increase by n.
        """
        return [self.pgn[i:i+n] for i in range(0, len(self.pgn), n)]


def main():
    bot = Bot()
    bot.connect()


if __name__ == '__main__':
    main()
