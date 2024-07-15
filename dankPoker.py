from texasholdem import Deck, evaluator, Card

class DankPokerGame:
    """
    Represents a Poker Game.
    Similar to Texas Hold'em, No blind bets.
    """
    def __init__(self, players: dict):
        self.players = {player: 
            {
            "hand": [], 
            "folded": False, 
            "bet": 0, 
            "chips": 1000,
            "acted": False
            } for player in players.keys()}
        self.pot = 0
        self.board = []  # community cards
        self.deck = Deck()
        self.currentMaxBet = 0
        self.currentTurnIndex = 0
        self.player_order = list(players.keys())
        self.phase = "flop" # Flop, Turn, River
        self.round = 0

    def get_chips(self, player: str) -> int:
        return self.players[player]["chips"]

    def start_new_round(self):
        self.currentMaxBet = 0
        self.pot = 0
        self.currentTurnIndex = 0
        self.deck = Deck()
        self.deck.shuffle()
        self.board = []
        self.round += 1
        self.canCheck = False
        for player in self.players:
            if self.players[player]["chips"] == 0:
                self.players.pop(player)
                continue
            self.players[player]["folded"] = False
            self.players[player]["bet"] = 0
            self.players[player]["hand"] = []
            self.players[player]["acted"] = False

    def deal_to_all_players(self):
        for player in self.players:
            self.players[player]["hand"] = self.deck.draw(2)

    def fold(self, player: str):
        self.players[player]["folded"] = True
        self.players[player]["acted"] = True
        self.next_turn()

    def bet(self, player: str, amount: int) -> bool:
        if self.players[player]["chips"] < amount:
            return False
        
        self.players[player]["bet"] += amount
        self.pot += amount
        self.players[player]["chips"] -= amount
        self.players[player]["acted"] = True
        if self.players[player]["bet"] > self.currentMaxBet:
            self.currentMaxBet = self.players[player]["bet"]
        self.next_turn()

        return True

    def call(self, player: str) -> bool:
        inc = self.currentMaxBet - self.players[player]["bet"]
        if self.players[player]["chips"] < inc:
            return False
        self.bet(player, inc)

    def check(self, player: str):
        if self.currentMaxBet == 0:
            self.players[player]["acted"] = True
            self.next_turn()
            return True
        else:
            return False

    def get_turn(self):
        return self.player_order[self.currentTurnIndex]
    
    def remove_player(self, player: str):
        self.players.pop(player)
        self.player_order.remove(player)
        if self.currentTurnIndex >= len(self.player_order):
            self.currentTurnIndex = 0

    def deal_flop(self):
        self.board.extend(self.deck.draw(3))

    def deal_turn(self):
        self.board.append(self.deck.draw(1)[0])
        self.currentMaxBet = 0

    def deal_river(self):
        self.board.append(self.deck.draw(1)[0])
        self.currentMaxBet = 0

    def next_turn(self):
        self.currentTurnIndex = (self.currentTurnIndex + 1) % len(self.player_order)
        while self.players[self.player_order[self.currentTurnIndex]]["folded"]:
            self.currentTurnIndex = (self.currentTurnIndex + 1) % len(self.player_order)

    def is_betting_round_complete(self):
        for player in self.players:
            if not self.players[player]["folded"] and (self.players[player]["bet"] < self.currentMaxBet or not self.players[player]["acted"]):
                return False
        # if true, then set acted to false for the turn/river.
        for player in self.players:
            self.players[player]["acted"] = False
        return True
    
    def one_left(self): # check if only one player left (everyone else folded)
        count = 0
        for player in self.players:
            if not self.players[player]["folded"]:
                count += 1
        return count == 1

    def get_winner(self) -> tuple: # return best player and name of hand
        best_hand = None
        best_player = None
        for player in self.players:
            if not self.players[player]["folded"]:
                hand_strength = evaluator.evaluate(cards=self.players[player]["hand"], board=self.board)
                if best_hand is None or hand_strength < best_hand:
                    best_hand = hand_strength
                    best_player = player
        return (best_player, evaluator.rank_to_string(best_hand))
    
    def distribute_chips(self):
        winner = self.get_winner()[0]
        self.players[winner]["chips"] += self.pot
        self.pot = 0

    
    def pretty_print(self, cards: list[Card]) -> str:
        formatted_cards = []
        suits = {
            "s": "Spades",
            "h": "Hearts",
            "d": "Diamonds",
            "c": "Clubs"
        }

        for card in cards:
            c = str(card).replace("T", "10")
            formatted_cards.append(f"{c[0]} of {suits[c[1]]}")

        return ", ".join(formatted_cards)
    
    def pretty_print_emojis(self, cards: list[Card]) -> str:
        rank_emojis = {
            "A": "🅰️", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣",
            "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "T": "🔟", "J": "J", "Q": "Q", "K": "K"
        }
        suit_emojis = {
            "s": "♠️",
            "h": "❤️",
            "d": "♦️",
            "c": "♣️"
        }
        
        formatted_cards = []
        
        for card in cards:
            c = str(card)
            rank = rank_emojis[c[0]]
            suit = suit_emojis[c[1]]
            formatted_cards.append(f"{rank}{suit}")

        return ", ".join(formatted_cards)


