import socket
import sys
import ssl
import time
import config
from chess_game import ChessGame
from pymongo.mongo_client import MongoClient
from Commands import (bot_info, date, help_ascii, ping, help_chess, source_code, play_chess, ro, r960, help_ro, pyramid, slow_pyramid,
                      news, help_news, daily, roulette, balance, leaderboard, help, shop, timeout, trophies, gemini, gemini2,
                      ascii, reloadglobals, reloadchannel, sparlerlink, suggest, poker, rm, olympics, summarize, describe, rottentomatoes, remind, eight_ball,
                      guessgame)


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
        self.cooldown = 3  # default cooldown for commands
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
        self.start_time = None  # to measure bot uptime
        # poker params
        self.pokerGameActive = False
        self.pokerGamePending = False
        self.pokerPlayers = {}  # username : userid
        self.pokerGame = None
        self.pokerTimer = None
        # guess game
        self.guessGameActive = False
        self.currentRound = 0
        self.gameEmotes = []
        self.numRounds = 5
        self.guessGameRoundTimer = None
        self.hintTimer = None

        # anyone can use these
        self.custom_commands = {
            'date': date.reply_with_date,
            'ping': ping.reply_to_ping,
            'help_chess': help_chess.reply_with_chesshelp,
            'source_code': source_code.reply_with_source_code,
            'play_chess': play_chess.play_chess,
            'bot': bot_info.reply_with_bot,
            'ro': ro.reply_with_random_opening,
            'r960': r960.reply_with_random960,
            'help_ro': help_ro.reply_with_help_ro,
            'pyramid': pyramid.reply_with_pyramid,
            'slow_pyramid': slow_pyramid.reply_with_slow_pyramid,
            'news': news.reply_with_news,
            'help_news': help_news.reply_with_help_news,
            'daily': daily.reply_with_daily,
            'roulette': roulette.reply_with_roulette,
            'balance': balance.reply_with_balance,
            'leaderboard': leaderboard.reply_with_leaderboard,
            'help': help.list_commands,
            'shop': shop.reply_with_shop,
            'timeout': timeout.reply_with_timeout,
            'trophies': trophies.reply_with_trophies,
            'gemini': gemini.reply_with_gemini,
            'gemini2': gemini2.reply_with_gemini_experimental,
            'ascii': ascii.reply_with_ascii,
            'help_ascii': help_ascii.reply_with_help_ascii,
            'reload_globals': reloadglobals.reload_global_emotes,
            'reload_channel': reloadchannel.reload_channel,
            'sparlerlink': sparlerlink.reply_with_sparlerlink,
            'suggest': suggest.reply_with_suggest,
            'poker': poker.reply_with_poker,
            'rm': rm.reply_with_rm,
            'olympics': olympics.reply_with_olympics,
            'summarize': summarize.reply_with_summarize,
            'describe': describe.reply_with_describe,
            'rt': rottentomatoes.reply_with_rottentomatoes,
            'remind': remind.reply_with_reminder,
            '8ball': eight_ball.reply_with_eight_ball,
            'guess': guessgame.reply_with_guess
        }

        # only bot owner can use these commands
        self.private_commands = {
            'leave': self.leave,
            'say': self.say,
            'echo': self.echo,
            'join_channel': self.join_channel,
            'leave_channel': self.part_channel,
            'reset_chess': self.reset_chess,
            'reset_poker': self.reset_poker

        }

        # commands for playing chess
        self.chess_commands = {
            'white': self.chooseSidePlayer1,
            'black': self.chooseSidePlayer1,
            'move': self.move,
            'join': self.join
        }
        self.dbClient = MongoClient(config.db_uri)
        self.db = self.dbClient['test']
        self.users = self.db['Users']

    def send_privmsg(self, channel, text):
        if text == self.last_msg and (time.time() - self.last_msg_time) < 30:
            text += ' \U000e0000'
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
        self.send_command('CAP REQ :twitch.tv/tags twitch.tv/commands')
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, config.initial_msg)
        self.start_time = time.time()
        self.loop_for_messages()

    def parse_message(self, message):
        parsed_message = {
            'tags': None,
            'source': None,
            'command': None,
            'parameters': None
        }

        idx = 0
        raw_tags_component = None
        raw_source_component = None
        raw_command_component = None
        raw_parameters_component = None

        # Parse tags component if it exists
        if message[idx] == '@':
            end_idx = message.find(' ')
            if end_idx == -1:
                return None
            raw_tags_component = message[1:end_idx]
            idx = end_idx + 1

        # Parse source component if it exists
        if message[idx] == ':':
            idx += 1
            end_idx = message.find(' ', idx)
            if end_idx == -1:
                return None
            raw_source_component = message[idx:end_idx]
            idx = end_idx + 1

        end_idx = message.find(':', idx)
        if end_idx == -1:
            end_idx = len(message)

        raw_command_component = message[idx:end_idx].strip()

        if end_idx != len(message):
            idx = end_idx + 1
            raw_parameters_component = message[idx:]

        parsed_message['command'] = self.parse_command(raw_command_component)

        if parsed_message['command'] is None:
            return None
        else:
            if raw_tags_component is not None:
                parsed_message['tags'] = self.parse_tags(raw_tags_component)

            parsed_message['source'] = self.parse_source(raw_source_component)
            parsed_message['parameters'] = raw_parameters_component

            # if message is a reply, remove leading @username
            if parsed_message['tags'] and parsed_message['tags'].get('reply-parent-msg-body'):
                raw_parameters_component = raw_parameters_component.split(' ')[
                    1:]
                raw_parameters_component = " ".join(raw_parameters_component)
                parsed_message['parameters'] = raw_parameters_component
                raw_parameters_component = raw_parameters_component + \
                    " " + parsed_message['tags']['reply-parent-msg-body']

            if raw_parameters_component and raw_parameters_component[0] == self.command_prefix:
                parsed_message['command'] = self.parse_parameters(
                    raw_parameters_component, parsed_message['command'])

        return parsed_message

    def parse_tags(self, tags):
        tags_to_ignore = {
            'client-nonce': None,
            'flags': None
        }

        dict_parsed_tags = {}
        parsed_tags = tags.split(';')

        for tag in parsed_tags:
            parsed_tag = tag.split('=', 1)
            tag_value = None if len(
                parsed_tag) == 1 or parsed_tag[1] == '' else parsed_tag[1]

            if parsed_tag[0] == 'reply-parent-msg-body':
                if tag_value:
                    tag_value = tag_value.replace('\\s', ' ')

            if parsed_tag[0] in ['badges', 'badge-info']:
                if tag_value:
                    dict_badges = {}
                    badges = tag_value.split(',')
                    for pair in badges:
                        badge_parts = pair.split('/')
                        dict_badges[badge_parts[0]] = badge_parts[1]
                    dict_parsed_tags[parsed_tag[0]] = dict_badges
                else:
                    dict_parsed_tags[parsed_tag[0]] = None
            elif parsed_tag[0] == 'emotes':
                if tag_value:
                    dict_emotes = {}
                    emotes = tag_value.split('/')
                    for emote in emotes:
                        emote_parts = emote.split(':')
                        text_positions = []
                        positions = emote_parts[1].split(',')
                        for position in positions:
                            position_parts = position.split('-')
                            text_positions.append({
                                'startPosition': position_parts[0],
                                'endPosition': position_parts[1]
                            })
                        dict_emotes[emote_parts[0]] = text_positions
                    dict_parsed_tags[parsed_tag[0]] = dict_emotes
                else:
                    dict_parsed_tags[parsed_tag[0]] = None
            elif parsed_tag[0] == 'emote-sets':
                dict_parsed_tags[parsed_tag[0]] = tag_value.split(',')
            else:
                if parsed_tag[0] not in tags_to_ignore:
                    dict_parsed_tags[parsed_tag[0]] = tag_value

        return dict_parsed_tags

    def parse_command(self, raw_command_component):
        parsed_command = None
        command_parts = raw_command_component.split(' ')

        if command_parts[0] in ['JOIN', 'PART', 'NOTICE', 'CLEARCHAT', 'HOSTTARGET', 'PRIVMSG']:
            parsed_command = {
                'command': command_parts[0],
                'channel': command_parts[1][1:]
            }
        elif command_parts[0] == 'PING':
            parsed_command = {'command': command_parts[0]}
        elif command_parts[0] == 'CAP':
            parsed_command = {
                'command': command_parts[0],
                'isCapRequestEnabled': (command_parts[2] == 'ACK')
            }
        elif command_parts[0] in ['GLOBALUSERSTATE', 'USERSTATE', 'ROOMSTATE']:
            parsed_command = {
                'command': command_parts[0],
                'channel': command_parts[1][1:] if len(command_parts) > 1 else None
            }
        elif command_parts[0] == 'RECONNECT':
            print(
                'The Twitch IRC server is about to terminate the connection for maintenance.')
            parsed_command = {'command': command_parts[0]}
        elif command_parts[0] == '421':
            print(f'Unsupported IRC command: {command_parts[2]}')
            return None
        elif command_parts[0] == '001':
            parsed_command = {
                'command': command_parts[0],
                'channel': command_parts[1][1:]
            }
        elif command_parts[0] in ['002', '003', '004', '353', '366', '372', '375', '376']:
            print(f'numeric message: {command_parts[0]}')
            return None
        else:
            print(f'\nUnexpected command: {command_parts[0]}\n')
            return None

        return parsed_command

    def parse_source(self, raw_source_component):
        if raw_source_component is None:
            return None
        else:
            source_parts = raw_source_component.split('!')
            return {
                'nick': source_parts[0] if len(source_parts) == 2 else None,
                'host': source_parts[1] if len(source_parts) == 2 else source_parts[0]
            }

    def parse_parameters(self, raw_parameters_component, command):
        command_parts = raw_parameters_component[1:].strip()
        params_idx = command_parts.find(' ')

        if params_idx == -1:
            command['botCommand'] = command_parts
            command['botCommandParams'] = None
        else:
            command['botCommand'] = command_parts[:params_idx]
            command['botCommandParams'] = command_parts[params_idx:].strip()
        return command

    def handle_message(self, received_msg):
        if received_msg == "None" or not received_msg:
            return
        # print(received_msg)
        message = self.parse_message(received_msg)
        print(f'> {message}')
        if not message:
            return
        if message['command']['command'] == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        if message['command']['command'] == 'RECONNECT':
            for channel in self.channels:
                self.send_privmsg(
                    channel, "The Twitch server needs to terminate the connection for maintenance. Reconnecting...")
            self.irc.shutdown(socket.SHUT_RDWR)
            self.irc.close()
            time.sleep(1)
            self.connect()

        # # Follow 1s cooldown
        if message['command']['command'] == 'PRIVMSG' and \
                message['parameters'][0] == (self.command_prefix) \
                and time.time() - self.time > 1:

            if message['command']['botCommand'].lower() in self.custom_commands:
                self.custom_commands[message['command']
                                     ['botCommand'].lower()](self, message)
                self.time = time.time()

            if message['command']['botCommand'].lower() in self.private_commands:
                self.private_commands[message['command']
                                      ['botCommand'].lower()](message)
                self.time = time.time()

            if message['command']['botCommand'].lower() in self.chess_commands:
                self.chess_commands[message['command']
                                    ['botCommand'].lower()](message)
                self.time = time.time()

            # Aliases.
            if message['command']['botCommand'].lower() == "commands":
                self.custom_commands["help"](self, message)
                self.time = time.time()

        # check for emotes when guess game active
        if message['command']['command'] == 'PRIVMSG' and self.guessGameActive:
            if not message['parameters']:
                return
            guess = message['parameters'].replace('\U000e0000', '')
            currentRoundEmote = guessgame.get_current_emote(self)
            if currentRoundEmote and guess == currentRoundEmote:
                if self.guessGameRoundTimer:
                    self.guessGameRoundTimer.cancel()
                if self.hintTimer:
                    self.hintTimer.cancel()
                name = message['tags']['display-name']
                m = f"{name} guessed it right! It's {currentRoundEmote}"
                self.send_privmsg(message['command']['channel'], m)
                time.sleep(1.1)
                if self.currentRound + 1 == self.numRounds:
                    # end the game
                    self.send_privmsg(
                        message['command']['channel'], "Game has ended.")
                    guessgame.reset_game(self)
                    return

                guessgame.start_new_round(self, message['command']['channel'])
            else:
                return

    def loop_for_messages(self):
        while True:
            received_msgs = self.irc.recv(4096).decode(errors='ignore')
            for received_msg in received_msgs.split('\r\n'):
                self.handle_message(received_msg)

    """Private commands"""

    def leave(self, message):
        text = 'forsenLeave Bot is shutting down.'
        if message['source']['nick'] == config.bot_owner:
            for channel in self.channels:
                self.send_privmsg(channel, text)
            sys.exit()
        else:
            if ("leave" not in self.state or time.time() - self.state["leave"] >
                    self.cooldown):
                self.state["leave"] = time.time()
                self.send_privmsg(message['command']
                                  ['channel'], "NOIDONTTHINKSO")

    def say(self, message):
        if message['source']['nick'] == config.bot_owner:
            self.send_privmsg(
                message['command']['channel'], message['command']['botCommandParams'])
        else:
            self.send_privmsg(message['command']['channel'], "No")

    # Use: #echo CHANNEL text, will send message text in specified channel.
    def echo(self, message):
        if message['source']['nick'] == config.bot_owner:
            if len(message['command']['botCommandParams']) > 1:
                text = message['command']['botCommandParams'].split()
                channel = text[0]
                text = " ".join(text[1:])
                if message['source']['nick'] == config.bot_owner:
                    self.send_privmsg(channel, text)

    # Work in progress.
    def join_channel(self, message):
        if message['source']['nick'] == config.bot_owner:
            newChannel = message['command']['botCommandParams']
            self.send_command(f'JOIN #{newChannel}')
            self.send_privmsg(newChannel, "forsenEnter")
            self.send_privmsg(message['command']['channel'], "Success")

    def part_channel(self, message):
        if message['source']['nick'] == config.bot_owner:
            newChannel = message['command']['botCommandParams']
            self.send_privmsg(newChannel, "forsenLeave")
            self.send_command(f'PART #{newChannel}')

            self.send_privmsg(message['command']['channel'], "Success")

    def reset_chess(self, message):
        if message['source']['nick'] == self.player1 or message['source']['nick'] == self.player2:
            self.chessGameActive = False
            self.gameAccepted = False
            self.send_privmsg(
                message['command']['channel'], "Chess game has been reset.")
            self.player1 = ""
            self.player2 = ""
            self.chessGameActive = False
            self.choseSidePlayer1 = False
            self.currentGame = None
            time.sleep(2)

    def reset_poker(self, message):
        if message['tags']['display-name'] in self.pokerPlayers:
            self.send_privmsg(
                message['command']['channel'], "Poker game has been reset.")
            self.pokerGameActive = False
            self.pokerPlayers = {}
            self.pokerGame = None
            self.pokerTimer = None
            time.sleep(0.9)

    # Runs if no one accepts chess challenge after 30s.
    def gameTimeout(self, channel):
        text = "No one accepted the challenge. :("
        self.send_privmsg(channel, text)
        self.chessGameActive = False
        self.player1 = ""

    """Functions for chess"""

    def join(self, message):  # join game
        if message['source']['nick'] != self.player1 and self.chessGameActive and not self.gameAccepted:
            self.chessTimer.cancel()
            text = f"@{message['tags']['display-name']} has joined the game."
            self.send_privmsg(message['command']['channel'], text)
            time.sleep(2)
            self.player2 = message['source']['nick']
            self.gameAccepted = True
            text = f"@{self.player1}, Choose a side: {self.command_prefix}white (white), {
                self.command_prefix}black (black)"
            self.send_privmsg(message['command']['channel'], text)
            time.sleep(2)

    def chooseSidePlayer1(self, message):
        # Player who started game chooses side first.
        if self.chessGameActive and self.player2 and message['source']['nick'] == self.player1 and not self.choseSidePlayer1:

            if message['command']['botCommand'].lower() == "white":
                self.choseSidePlayer1 = True
                text = f"@{self.player1}, you will play as white"
                self.send_privmsg(message['command']['channel'], text)
                time.sleep(2)
                text = f"@{self.player1}, you are starting, enter start move."
                self.send_privmsg(message['command']['channel'], text)
                self.currentGame = ChessGame(self.player1, self.player2)
                time.sleep(2)

            elif message['command']['botCommand'].lower() == "black":
                text = f"@{self.player1}, you will play as black"
                self.send_privmsg(message['command']['channel'], text)
                time.sleep(2)
                text = f"@{self.player2}, you are starting, enter start move."
                self.send_privmsg(message['command']['channel'], text)
                self.currentGame = ChessGame(self.player2, self.player1)
                time.sleep(2)
            else:
                text = f"Invalid input, please enter \
                either {self.command_prefix}white or {self.command_prefix}black."
                self.send_privmsg(message['command']['channel'], text)
                time.sleep(2)

    # Start the game

    def move(self, message):
        if self.currentGame and \
           ("move" not in self.state or time.time() - self.state["move"] > 2):

            self.state["move"] = time.time()

            # White to play
            if self.currentGame.current_side == 'w':
                if message['source']['nick'] == self.currentGame.player1:
                    if not message['command']['botCommandParams']:
                        self.send_privmsg(
                            message['command']['channel'], f'@{self.currentGame.player1}, please enter a move!')
                    else:
                        move = message['command']['botCommandParams']
                        if move == "resign":
                            self.currentGame.resign(
                                message['source']['nick'])  # will update pgn
                            text = f"@{message['tags']['display-name']
                                       } resigned. @{self.currentGame.player2} wins."
                            self.send_privmsg(
                                message['command']['channel'], text)
                            time.sleep(2)
                            # get pgn
                            pgn = self.currentGame.get_pgn()
                            for m in pgn:
                                self.send_privmsg(
                                    message['command']['channel'], m)
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
                            if self.currentGame.game_over():
                                result = self.currentGame.result()
                                self.send_privmsg(
                                    message['command']['channel'], result)
                                time.sleep(2)
                                for m in self.currentGame.get_pgn():  # print PGN
                                    self.send_privmsg(
                                        message['command']['channel'], m)
                                    time.sleep(2)
                                self.chessGameActive = False
                                self.choseSidePlayer1 = False
                                self.gameAccepted = False
                                self.currentGame = None
                                self.player1 = ""
                                self.player2 = ""
                                return
                            # if game not over, print PGN, black to play.
                            for m in self.currentGame.get_pgn():
                                self.send_privmsg(
                                    message['command']['channel'], m)
                                time.sleep(2)
                            self.send_privmsg(
                                message['command']['channel'], f"@{self.currentGame.player2} it is your turn.")

                        else:  # move was unsuccessful
                            text = f"Invalid/illegal move, please try again. \
                            For help refer to {self.command_prefix}help_chess."
                            self.send_privmsg(
                                message['command']['channel'], text)
                            time.sleep(2)

            elif self.currentGame.current_side == 'b':

                if message['source']['nick'] == self.currentGame.player2:
                    if not message['command']['botCommandParams']:
                        self.send_privmsg(
                            message['command']['channel'], f'@{self.currentGame.player2}, please enter a move!')
                    else:
                        move = message['command']['botCommandParams']
                        if move == "resign":
                            self.currentGame.resign(
                                message['source']['nick'])  # will update pgn
                            text = f"@{message['tags']['display-name']} resigned. @{
                                self.currentGame.player1} wins! PogChamp"
                            self.send_privmsg(
                                message['command']['channel'], text)
                            time.sleep(2)
                            pgn = self.currentGame.get_pgn()
                            for m in pgn:
                                self.send_privmsg(
                                    message['command']['channel'], m)
                                time.sleep(2)
                            self.chessGameActive = False
                            self.choseSidePlayer1 = False
                            self.gameAccepted = False
                            self.currentGame = None
                            self.player1 = ""
                            self.player2 = ""
                            return
                        moveSuccesful = self.currentGame.move(move)
                        if moveSuccesful:
                            if self.currentGame.game_over():
                                result = self.currentGame.result()
                                self.send_privmsg(
                                    message['command']['channel'], result)
                                for m in self.currentGame.get_pgn():  # print PGN
                                    self.send_privmsg(
                                        message['command']['channel'], m)
                                    time.sleep(2)
                                self.chessGameActive = False
                                self.gameAccepted = False
                                self.choseSidePlayer1 = False
                                self.currentGame = None
                                self.player1 = ""
                                self.player2 = ""
                                return
                            for m in self.currentGame.get_pgn():
                                self.send_privmsg(
                                    message['command']['channel'], m)
                                time.sleep(2)
                            self.send_privmsg(
                                message['command']['channel'], f"@{self.currentGame.player1} it is your turn.")

                        else:  # move was unsuccessful
                            text = f"Invalid/illegal move, please try again. \
                            For help refer to {self.command_prefix}help_chess."
                            self.send_privmsg(
                                message['command']['channel'], text)
                            time.sleep(2)


def main():
    bot = Bot()
    bot.connect()


if __name__ == '__main__':
    main()
