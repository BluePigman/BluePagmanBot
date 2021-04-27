"""
This module contains functions that check if a chess
move makes sense, and if a promotion move is valid.
"""


def checkInput(move): # Check if a move makes sense (right format)
    numbers = "12345678"
    letters = "abcdefgh"
    try:
        if move[0] not in letters or move[1] not in numbers:
            return False
        elif move[2] not in letters or move[3] not in numbers:
            return False
    
        return True

    except:
        return False

def checkPromotion(move): # Check if a promotion move is valid.
    symbols = "bkqr"
    return move[4:] in symbols
