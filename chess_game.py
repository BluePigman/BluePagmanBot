import chess, time
from threading import Timer

class ChessGame:
    def __init__(self, player1, player2):
        self.board = chess.Board()
        self.player1 = player1  # player 1 is white, player 2 is black
        self.player2 = player2
        self.pgn = ""
        self.current_side = "w"
        self.move_count = 0
        self.increment = 0

    def switch_side(self):
        if self.current_side == "w":
            self.current_side = "b"
            return
        self.current_side = "w"

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
            # Ensure the move is valid before trying to get SAN
            uci_move = self.board.parse_san(move)
            san_move = self.board.san(uci_move) # Get the proper SAN notation

            if self.increment % 2 == 0:
                self.move_count += 1
                self.pgn += str(self.move_count) + ". " + san_move + " "
            else:
                self.pgn += san_move + " "

            self.board.push(uci_move) # Use the validated UCI move
            self.increment += 1
            self.switch_side()
            return True
        except:
            return False

    def get_pgn(self):
        return self.split_pgn()

    def resign(self, player):
        if player == self.player1: # White resigns
           return "0-1"
        else: # Black resigns
           return "1-0"


    def game_over(self):
        return self.board.is_game_over(claim_draw=True)


    def result(self, resignation_result=None):
        """ Return the result of the game in a string. (Player1 wins/Player2 wins/
        stalemate/draw by insufficient material/resignation"""
        outcome = self.board.outcome(claim_draw=True)

        if resignation_result: # Handle resignation passed from the manager
             if resignation_result == "1-0":
                 self.pgn += ' { White wins by resignation. } 1-0'
                 return f"@{self.player2} resigned. @{self.player1} wins! PogChamp"
             elif resignation_result == "0-1":
                 self.pgn += ' { Black wins by resignation. } 0-1'
                 return f"@{self.player1} resigned. @{self.player2} wins! PogChamp"

        if outcome:
            termination_reason = str(outcome.termination).split('.')[-1].replace("_", " ").lower() # e.g., "Termination.CHECKMATE" -> "checkmate"
            if outcome.winner == chess.WHITE:
                self.pgn += f' {{ White wins by {termination_reason}. }} 1-0'
                return f"{termination_reason.capitalize()}, @{self.player1} wins! PogChamp"
            elif outcome.winner == chess.BLACK:
                self.pgn += f' {{ Black wins by {termination_reason}. }} 0-1'
                return f"{termination_reason.capitalize()}, @{self.player2} wins! PogChamp"
            else: # Draw
                self.pgn += f' {{ Draw by {termination_reason}. }} 1/2-1/2'
                # Customize draw messages
                if outcome.termination == chess.Termination.STALEMATE:
                    return "Stalemate LUL"
                elif outcome.termination == chess.Termination.INSUFFICIENT_MATERIAL:
                     return "Draw by insufficient material."
                elif outcome.termination == chess.Termination.FIVEFOLD_REPETITION:
                     return "Draw by fivefold repetition."
                else: # Other draws (threefold repetition if claim_draw=True, seventyfive moves)
                     return f"Draw by {termination_reason}."
        return "Game is ongoing." # Should not happen if game_over() is true unless resigning


    def get_san(self, move):
        """
        Get standard algebraic notation of move (e2e4 becomes e4).
        move is a uci representation of move.
        """
        return self.board.san(move)


    def split_pgn(self):
        """Split the long PGN message into a list of under 500 character messages."""
        # Get substrings from i to specified length n, put into list. For loop from 0 to length of pgn, increase by n
        n = 490 
        return [self.pgn[i:i+n] for i in range(0, len(self.pgn), n)]


class ChessManager:
    def __init__(self, bot_instance):
        self.bot = bot_instance  # Reference to the main bot instance to send messages
        self.prefix = bot_instance.prefix
        self.chessGameActive = False
        self.gameAccepted = False
        self.player1 = ''
        self.player2 = ''
        self.choseSidePlayer1 = False
        self.currentGame = None  # Holds the ChessGame instance
        self.chessTimer = None   
        self.join_timeout_duration = 30 

        self.commands = {
            'join': self.join,
            'white': self.chooseSidePlayer1,
            'black': self.chooseSidePlayer1,
            'move': self.move,
            'resign': self.resign
        }


    def _send_message(self, channel, text):
        """Helper function to send messages via the bot."""
        self.bot.send_privmsg(channel, text)
        time.sleep(1.5) 


    def start_game(self, message):
        if self.chessGameActive:
            self._send_message(message['command']['channel'], "A chess game is already in progress.")
            return

        self.chessGameActive = True
        self.player1 = message['source']['nick']
        display_name = message['tags'].get('display-name', self.player1)

        self._send_message(
            message['command']['channel'],
            f"@{display_name} has started a chess game. Type {self.prefix}join to join the game."
        )

        self.chessTimer = Timer(
            self.join_timeout_duration,
            self.gameTimeout,
            args=[message['command']['channel'],]
        )
        self.chessTimer.start()


    def gameTimeout(self, channel):
        self._send_message(channel, f"No one accepted the challenge. :(")
        self.chessGameActive = False


    def handle_command(self, command_name, message):
        """Dispatches chess commands to the appropriate methods."""
        command_func = self.commands.get(command_name.lower())
        if command_func:
            if not self.chessGameActive and command_name != 'join':
                 if not (command_name == 'join' and self.chessGameActive and not self.gameAccepted):
                    return
            try:
                command_func(message)
            except Exception as e:
                print(f"Error processing chess command '{command_name}' from {message['source']['nick']}: {e}")
        else:
            print(f"Unknown chess command received: {command_name}")
            return


    def join(self, message):
        channel = message['command']['channel']
        joiner_nick = message['source']['nick']
        joiner_display_name = message['tags'].get('display-name', joiner_nick)

        if joiner_nick == self.player1:
            self._send_message(channel, f"@{joiner_display_name}, you can't join your own game!")
            return
        
        if message['source']['nick'] != self.player1 and self.chessGameActive and not self.gameAccepted:
            self.chessTimer.cancel()
            text = f"@{joiner_display_name} has joined the game."
            self._send_message(channel, text)
            time.sleep(2)
            self.player2 = joiner_nick
            self.gameAccepted = True
            text = f"@{self.player1}, Choose your side: {self.prefix}white or  {self.prefix}black"
            self._send_message(channel, text)
            time.sleep(2)


    def chooseSidePlayer1(self, message):
        """Allows player 1 to choose their color after player 2 joins."""
        channel = message['command']['channel']
        command = message['command']['botCommand'].lower()
        
        # Player who started game chooses side first.
        if self.chessGameActive and self.player2 and message['source']['nick'] == self.player1 and not self.choseSidePlayer1:
        
            if command == "white":
                self.choseSidePlayer1 = True
                self.currentGame = ChessGame(self.player1, self.player2) # P1=White, P2=Black
                self._send_message(channel, f"@{self.player1}, you will play as White.")
                time.sleep(2)
                self._send_message(channel, f"@{self.player1}, it's your turn to move! Use {self.prefix}move <move> (e.g., {self.prefix}move e4)")

            elif command == "black":
                self.choseSidePlayer1 = True
                self.currentGame = ChessGame(self.player2, self.player1) # P2=White, P1=Black
                self._send_message(channel, f"@{self.player1}, you will play as Black.")
                time.sleep(2)
                self._send_message(channel, f"@{self.player2}, you will play as White. It's your turn to move! Use {self.prefix}move <move>")


    def _end_game(self, channel, result_message):
        self._send_message(channel, result_message)
        time.sleep(1)
        if self.currentGame:
             pgn_parts = self.currentGame.get_pgn()
             if pgn_parts:
                 self._send_message(channel, "Final PGN:")
                 for part in pgn_parts:
                     self._send_message(channel, part)
                     time.sleep(1)
        self.chessGameActive = False


    def resign(self, message):
        """Handles a player resigning."""
        channel = message['command']['channel']
        sender_nick = message['source']['nick']

        if not self.currentGame:
             return 

        resignation_result_code = None
        result_message = ""

        if sender_nick == self.currentGame.player1: # Player 1 (White in currentGame) resigns
            resignation_result_code = "0-1"
            result_message = self.currentGame.result(resignation_result=resignation_result_code)

        elif sender_nick == self.currentGame.player2: # Player 2 (Black in currentGame) resigns
            resignation_result_code = "1-0"
            result_message = self.currentGame.result(resignation_result=resignation_result_code)
        else:
             return

        if result_message:
             self._end_game(channel, result_message)


    def move(self, message):
        """Handles a player making a move."""
        channel = message['command']['channel']
        sender_nick = message['source']['nick']
        sender_display_name = message['tags'].get('display-name', sender_nick)

        if not self.currentGame or not self.gameAccepted or not self.choseSidePlayer1:
             return

        current_player_nick = None
        opponent_player_nick = None
        if self.currentGame.current_side == 'w':
            current_player_nick = self.currentGame.player1 # White's turn
            opponent_player_nick = self.currentGame.player2
        else:
            current_player_nick = self.currentGame.player2 # Black's turn
            opponent_player_nick = self.currentGame.player1

        if sender_nick != current_player_nick:
            return

        # Get the move string
        move_san = message['command'].get('botCommandParams')
        if not move_san:
            self._send_message(channel, f'@{sender_display_name}, please enter a move! (e.g., {self.prefix}move e4)')
            return

        move_successful = self.currentGame.move(move_san)

        if move_successful:
            if self.currentGame.game_over():
                result = self.currentGame.result()
                self._end_game(channel, result)
            else:
                pgn_parts = self.currentGame.get_pgn()
                if pgn_parts: 
                     for part in pgn_parts:
                         self._send_message(channel, part)
                         time.sleep(1) 
                self._send_message(channel, f"@{opponent_player_nick}, it is your turn.")

        else:
            self._send_message(
                channel,
                f"@{sender_display_name}, Invalid/illegal move, please try again. For help refer to {self.prefix}help_chess."
            )
            time.sleep(0.5)