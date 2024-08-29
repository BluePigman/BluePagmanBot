import chess

class ChessGame:
    def __init__(self, player1, player2):
        self.board = chess.Board()
        self.player1 = player1  # player 1 is white, player 2 is black
        self.player2 = player2
        self.pgn = ""
        self.current_side = "w"
        self.move_count = 0
        self.increment = 0
        self.user_quit = False

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
            uci = self.board.parse_san(move)  # convert SAN to UCI

            if self.increment % 2 == 0:
                self.move_count += 1
                self.pgn += str(self.move_count) + ". " +  \
                    self.get_san(uci) + " "
            else:
                self.pgn += self.get_san(uci) + " "
            self.board.push_san(move)
            self.increment += 1
            self.switch_side()
            return True
        except:
            return False

    def get_pgn(self):
        return self.split_pgn()

    def resign(self, player):
        if player == self.player1:
            self.pgn = self.pgn + "{ White resigns. } 0-1"
        else:
            self.pgn = self.pgn + " { Black resigns. } 1-0"

    def reset(self):
        self.player1 = ""
        self.player2 = ""
        self.board.reset()
        self.pgn = ""
        self.current_side = "w"
        self.move_count = 0
        self.increment = 0

    def game_over(self):
        """Return if the game is over (by checkmate, stalemate,
        draw by insufficient material, or draw by fivefold repetition)"""
        return self.board.is_checkmate() or self.board.is_stalemate() or \
            self.board.is_insufficient_material() or self.board.is_fivefold_repetition()

    def result(self):
        """ Return the result of the game in a string. (Player1 wins/Player2 wins/
        stalemate/draw by insufficient material"""
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
            self.pgn += ' { The game is a draw. } 1/2-1/2'
            result = "Draw by insufficient material."
            return result

        else:  # Fivefold repetition
            self.pgn += ' { The game is a draw. } 1/2-1/2'
            result = "Draw by fivefold repetition."
            return result

    def get_san(self, move):
        """
        Get standard algebraic notation of move (e2e4 becomes e4).
        move is a uci representation of move.
        """
        return self.board.san(move)

    def split_pgn(self):
        """Split the long PGN message into a list of under 500 character messages.
        """
        n = 500
        """ Get substrings from i to specified length n, put into list.
        For loop from 0 to length of pgn, increase by n.
        """
        return [self.pgn[i:i+n] for i in range(0, len(self.pgn), n)]
