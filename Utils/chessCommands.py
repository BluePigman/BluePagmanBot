import random
"""
This module contains functions for getting random chess openings and chess 960 FENs.
"""


def getRandomOpening():
    # https://stackoverflow.com/a/3540346
    # Get random opening in list of openings
    lines = open('Chess Openings.txt').read().splitlines()  # list
    myline = random.choice(lines)
    return myline.rstrip()


def getRandomOpeningSpecific(name, side=None):
    # https://stackoverflow.com/a/26112713
    # Get random opening with specified name and/or side
    with open('Chess Openings.txt', 'r') as f:
        if side == 'w':
            whiteOpenings = [line for line in f if " - w " in line]
            targets = [line for line in whiteOpenings
                       if name.lower() in line.lower()]

            if not targets:
                return "No openings found."

            result = random.choice(targets)
            return result.rstrip()

        elif side == 'b':
            blackOpenings = [line for line in f if " - b " in line]
            targets = [line for line in blackOpenings if
                       name.lower() in line.lower()]

            if not targets:
                return "No openings found."

            result = random.choice(targets)
            return result.rstrip()

        else:

            targets = [line for line in f if name.lower() in line.lower()]
            if not targets:
                return "No openings found."
            result = random.choice(targets)
            return result.rstrip()


def getRandom960():  # Get random 960 position.
    lines = open('chess960 FENS.txt').read().splitlines()
    myline = random.choice(lines)
    return myline.rstrip()
