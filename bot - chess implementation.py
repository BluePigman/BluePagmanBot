import socket
import sys
import ssl
import datetime
import json
from collections import namedtuple
import time
import random
import config
import chess

Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args',
)


def remove_prefix(string, prefix):
    if not string.startswith(prefix):
        return string
    return string[len(prefix):]

board = chess.Board()
board.reset()

    
player1 = None
player2 = None

class Bot:
    
    def __init__(self):
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6697
        self.oauth_token = config.OAUTH_TOKEN
        self.username = config.username
        self.channels = config.channels
        self.command_prefix = config.prefix
        self.state = {}
        
        self.custom_commands = {
            'date': self.reply_with_date,
            'ping': self.reply_to_ping,
            'help': self.list_commands,
            'help_chess': self.reply_with_chesshelp,
            'source_code': self.reply_with_source_code,
            'play_chess': self.play_chess
        }

        self.private_commands = {
            'leave': self.leave
        }

        self.chess_commands = {
            'join': self.join,
            'white': self.chooseSidePlayer1,
            'black': self.chooseSidePlayer1
        }


    def init(self):
        self.connect()

    def send_privmsg(self, channel, text):
        self.send_command(f'PRIVMSG #{channel} :{text}')

    def send_command(self, command):
        if 'PASS' not in command:       
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode())

    def connect(self):
        self.irc = ssl.wrap_socket(socket.socket())
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
                text_command = remove_prefix(text_parts[0], self.command_prefix)
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

    def reply_with_date(self, message):
        formatted_date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        text = f'{message.user}, the date is {formatted_date} EST.'
        self.send_privmsg(message.channel, text)

    def reply_to_ping(self, message):
        text = f'@{message.user}, forsenEnter'
        self.send_privmsg(message.channel, text)
    
    def reply_with_chesshelp(self, message):
        text = (f'@{message.user}, Work in progress. Chess game made by @Bluepigman5000. \
                Computer will play random moves. To make a move, type the piece, \
                you want to move followed by the square you want to go to, \
                same applies for captures. For example a game could go like: \
                1. e2e4 f7f5 2. d1h5 g7g6 3. f1e2 g6h5 4. e2h5.')
         
        self.send_privmsg(message.channel, text)
        self.send_privmsg(message.channel, 'For promotions, add the letter of the piece\
                you would like to promote to at the end (e.g. g7h8q).') 

    def reply_with_source_code(self, message):
        self.send_privmsg(message.channel, 'Source code: \
                          https://github.com/BluePigman/BluePagmanBot') 
        

    def list_commands(self, message):
        custom_cmd_names = list(self.custom_commands.keys())
        all_cmd_names = [
            self.command_prefix + cmd
            for cmd in custom_cmd_names
        ]
        text = "" f'@{message.user}, Commands: ' + ' '.join(all_cmd_names)
        self.send_privmsg(message.channel, text)
            
    def handle_message(self, received_msg):
        if len(received_msg) == 0:
            return

        message = self.parse_message(received_msg)
        # print(f'> {message}')
        #print(f'> {received_msg}')

        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        if message.irc_command == 'PRIVMSG':
            if message.text_command in self.custom_commands:
                self.custom_commands[message.text_command](message)

            if message.text_command in self.private_commands:
                self.private_commands[message.text_command](message)
                
            if message.text_command in self.chess_commands:
                self.chess_commands[message.text_command](message)

    def loop_for_messages(self):
        while True:
            received_msgs = self.irc.recv(2048).decode()
            for received_msg in received_msgs.split('\r\n'):
                self.handle_message(received_msg)
        
    def leave (self, message):
        text = 'forsenLeave'
        if message.user == "bluepigman5000":
            self.send_privmsg(message.channel, text)
            sys.exit()


    """
    Chess stuff here
    """
    #Global Variables
    global chessGameActive
    chessGameActive = False
    global player2Joined
    player2Joined = False
    global choseSide
    choseSide = False
    # First user to start the initial game, return player
    def getPlayer1(self, message):
        global chessGameActive
        if not chessGameActive:
            chessGameActive = True
            text = f'@{message.user} has started a chess game. Type #join to join \
                the game.'
            self.send_privmsg(message.channel, text)
            global player1
            player1 = message.user
            

    #Player 2 that joins the game.
    def getPlayer2(self, message, chessGameActive):
        global player2Joined
        if (chessGameActive == True and player2Joined == False):
            player2Joined = True
            text = f'@{message.user} has joined the game.'
            self.send_privmsg(message.channel, text)
            global player2
            player2 =  message.user
            text = f"@{player1}, Choose a side: #white (white), #black (black)"
            self.send_privmsg(message.channel, text)

    #Player who started game chooses side first.
    def chooseSidePlayer1(self, message):
        global choseSide
        
        if chessGameActive and not choseSide:
            choseSide = True
            if message.user == player1:

                global player1Color
                global player2Color
                if message.text_command == "white".lower():
                    text = f"@{player1}, you will play as white"
                    self.send_privmsg(message.channel, text)
                            
                    player1Color = "w"
                    player2Color = "b"                
        
                elif message.text_command == "black".lower():
                    text = f"@{player1}, you will play as black"
                    self.send_privmsg(message.channel, text)
                    player1Color = "b"
                    player2Color = "w"
                
                else:
                    text = "Invalid input, please enter \
                    either w for white or b for black."
                    self.send_privmsg(message.channel, text)
    # Command for when someone types #play
    def play_chess(self,message):
            self.getPlayer1(message)

    # DO this when someone types #join
    def join(self,message):
        if chessGameActive:
            self.getPlayer2(message, chessGameActive)
            self.chessGame
            
    # Start the game
    def chessGame(self):
        """Print @Player1, enter your move in long algebraic notation,
        with no hyphen. Example #move e2e4. For captures, simply enter start
        square and end square, no x.
        For promotions, add the desired piece's letter at the end in
        LOWERCASE
        (#move a7a8q)

        General Idea: Start filtering all messages, the ones with #move are the
        ones that we will consider. Also check if it is from Player1 or Player2,
        at their specific turn.

        Once we get the player's move, we must strip #move to get only the
        algebraic notation of the move. Then check if it is a legal move using
        chess-python module's list of legal moves on the board.

        Any string longer than 5 representing the move does not make sense, so
        tell @Player invalid move, try again.

        If the move is not legal, then tell them move is not legal.
        


        
        """
        
              
def main():
    bot = Bot()
    bot.init()

if __name__ == '__main__':
    main()







