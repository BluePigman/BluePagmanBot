import random
"""
This module contains functions that check if a chess
move makes sense, and if a promotion move is valid.

stackoverflow.com/questions/3540288/how-do-i-read-a-random-line-from-one-file
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
    lines = open('Chess Openings.txt').read().splitlines()
    myline =random.choice(lines)
    return myline

def getJoke(x): #return setup and punchline.
    setups = open('Joke Setup.txt')
    punchlines = open('Joke Punchline.txt')
    #x = random.randint(0,84)
    
    # read the content of the file opened
    setup = setups.readlines()
    punchline = punchlines.readlines()

    return (setup[x], punchline[x])
    
