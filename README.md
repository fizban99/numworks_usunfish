# μSunfish Chess for the NumWorks
Chess game for the NumWorks calculator in micropython based on Sunfish

The [Sunfish engine](https://github.com/thomasahle/sunfish) has been ported to micropython to be able to work decently on devices with limited memory.

It has 7 levels of difficulty (use Ln to change levels or "N" on the desktop) and you can undo the last move (only the last one, with backspace).
Use Pi (or "P" on the desktop) to switch to black (rotates the board and makes the engine move) 
You select the piece to move with the cursor keys and OK (or "Enter" on the Desktop). You can cancel the move selecting again the piece.

Requires the usunfish_engine.py to be also loaded in the calculator.
This version can be run on a PC.

You can find the minified NumWorks version at [my repository - usunfish_chess](https://my.numworks.com/python/fizban/usunfish_chess) and [my repository - usunfish_engine](https://my.numworks.com/python/fizban/usunfish_engine). You have to send both files to the calculator and execute usunfish_chess.py


You can play directly on your browser thanks to pyodide integration of pygame (it takes some time for the initial load):
[online NumWorks uSunfish](https://fizban99.github.io/numworks_usunfish/app)


![Screenshot](img/screenshot.png)


## Features
- 7 levels of difficulty based on a maximum of nodes evaluated (from 125 in level 0 up to 8000 nodes in level 6)
- Reduced memory footprint in the NumWorks by extensively using some micropython features such as string interning and 31-bit smallints and removing the object-oriented approach of the original Sunfish.
- Although it has no hash table, it has a small cache to effectively reduce the node traversing time on sequential iterations during the iterative deepening MTD-bi search
- Since it has no hash table, it uses a slightly modified pst for each move, to prevent the moves from being too deterministic.
- It contains a small opening book of 1452 plies based on the [Balsa_270423.pgn](https://sites.google.com/site/computerschess/balsa-suite-270423) openings file.
- As a reply of non-common openings, it has 5 different answers to non-common starting positions using the 400 moves.pgn file from [https://www.scacchi64.com/downloads.html](https://www.scacchi64.com/downloads.html)
- The hardest level is aligned with an ELO 1450 against the Patricia engine simulating that ELO. This engine easily beats the [badger2040 port](https://github.com/niutech/chess-badger2040).
- The pst tables are directly loaded from a base64-encoded string to save code space
- It adds an end-game pst table for the king, using its [PeSTO version](https://www.chessprogramming.org/PeSTO%27s_Evaluation_Function).
- Instead of a string, the board is a 64-item list that is part of the global position. Although a list to store the board is memory-hungry, its updatable and faster for restoring the difference when returning from a recursive call.