import random
import string
"""
This module contains functions that check if a chess
move makes sense, and if a promotion move is valid.

https://stackoverflow.com/a/3540346
https://stackoverflow.com/a/26112713
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


def getRandomOpening(): # Get random opening in list of openings
    lines = open('Chess Openings.txt').read().splitlines() #list
    myline = random.choice(lines)
    return myline

def getRandomOpeningSpecific(name, side = None):
    # Get random opening with specified name and/or side
    with open('Chess Openings.txt', 'r') as f:
        if side == 'w':
            whiteOpenings = [line for line in f if " - w " in line]
            targets = [line for line in whiteOpenings \
                       if name.lower() in line.lower()]
            
            if not targets:
                return "No openings found."
            
            result = random.choice(targets)
            return result
        
        elif side == 'b':
            blackOpenings = [line for line in f if " - b " in line]
            targets = [line for line in blackOpenings if \
                       name.lower() in line.lower()]
            
            if not targets:
                return "No openings found."
            
            result = random.choice(targets)
            return result
        
        else:
            
        
            targets = [line for line in f if name.lower() in line.lower()]
            if not targets:
                return "No openings found."
            result = random.choice(targets)
            return result

"""targets = [line for line in f if name in line]
        result = random.choice(targets)
        return result
"""

def getJoke(x): #return setup and punchline.
    setups = open('Joke Setup.txt')
    punchlines = open('Joke Punchline.txt')
    #x = random.randint(0,84)
    
    # read the content of the file opened
    setup = setups.readlines()
    punchline = punchlines.readlines()

    return (setup[x], punchline[x])

def getRandom960(): # Get random 960 position.
    lines = open('chess960 FENS.txt').read().splitlines()
    myline =random.choice(lines)
    return myline
