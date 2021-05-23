"""Get the important parts out of TSV, put into text file
"""
import csv
import chess

with open("a.tsv") as fd: #repeat for a, b, c, d, e,
    #remove blank line at end after each operation.
    rd = csv.reader(fd, delimiter="\t", quotechar='"')
    next(fd)
    file = open("Chess Openings.txt", "a")
    for row in rd:
        uciMoves = row[3].split()
        moveOrder = ""
        moveCount = 0
        increment = 0
        board = chess.Board()
        for uci in uciMoves:
            move = chess.Move.from_uci(uci)
            if increment % 2 == 0:
                moveCount += 1
                moveOrder += str(moveCount) + ". " + \
                board.san(move) + " "
                
            else:
                moveOrder += board.san(move) + " "
                
            board.push(move)
            increment += 1
        file.write(row[1] + " - " + moveOrder + "\n")

file.close()
