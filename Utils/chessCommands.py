import random
from pathlib import Path
"""
This module contains functions for getting random chess openings and chess 960 FENs.
"""

base_dir = Path(__file__).resolve().parent  # Directory containing chessCommands.py
chess_openings_path = (base_dir / ".." / "Data" / "Chess Openings.txt").resolve()

openings_960_path = (base_dir / ".." / "Data" / "chess960 FENS.txt").resolve()

def getRandomOpening():
    # https://stackoverflow.com/a/3540346
    # Get random opening in list of openings
    lines = open(chess_openings_path).read().splitlines()  # list
    myline = random.choice(lines)
    return myline.rstrip()


def getRandomOpeningSpecific(name, side=None):
    # https://stackoverflow.com/a/26112713
    # Get random opening with specified name and/or side
    with open(chess_openings_path, 'r') as f:
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
    lines = open(openings_960_path).read().splitlines()
    myline = random.choice(lines)
    return myline.rstrip()
