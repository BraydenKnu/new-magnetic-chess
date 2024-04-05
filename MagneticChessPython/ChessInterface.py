"""
CHESS INTERFACE

Interface between the user, engine, and the PhysicalBoard class.


COORDINATE SYSTEM
    - Bank1Bank2   Main Board
    - _________ _________________
    8 |_|_|_|_| |_|_|_|_|_|_|_|_|
    7 |_|_|_|_| |_|_|_|_|_|_|_|_|
    6 |_|_|_|_| |_|_|_|_|_|_|_|_|
    5 |_|_|_|_| |_|_|_|_|_|_|_|_|
    4 |_|_|_|_| |_|_|_|_|_|_|_|_|
y   3 |_|_|_|_| |_|_|_|_|_|_|_|_|
^   2 |_|_|_|_| |_|_|_|_|_|_|_|_|
|   1 |_|_|_|_| |_|_|_|_|_|_|_|_|
|      w x y z   a b c d e f g h
|     -5-4-3-2 _ 0 1 2 3 4 5 6 7 (file)
+-----> x
^
(0, 0)

BANK PIECES
upper case = white, lower case = black
p = pawn, r = rook, n = knight, b = bishop, q = queen, k = king
    -   Bank1   Bank2
    - +---+---+---+---+
    8 | P | Q | q | p |
    - +---+---+---+---+
    7 | P | Q | q | p |
    - +---+---+---+---+
    6 | P | R | r | p |
    - +---+---+---+---+
    5 | P | R | r | p |
    - +---+---+---+---+
    4 | P | B | b | p |
    - +---+---+---+---+
    3 | P | B | b | p |
    - +---+---+---+---+
    2 | P | N | n | p |
    - +---+---+---+---+
    1 | P | N | n | p |
    - +---+---+---+---+
        w   x   y   z

BANK FILL ORDER: Higher ranks are filled first.
"""

# Imports
import os
import chess                    # (pip install python-chess) Documentation: https://python-chess.readthedocs.io/en/latest/
import chess.engine             # (pip install python-chess) Documentation: https://python-chess.readthedocs.io/en/latest/
import random
import time
from PhysicalBoard import PhysicalBoard
from Audio import Audio

# Configuration
MOVE_VALIDITY_THRESHOLD = 1 # Time to wait (in seconds) after a human move to consider it finished.
COMPUTER_MOVE_DELAY = 1 # (in seconds) Wait this long after the last move is finished before making a computer move.

# Constants
RANKS = "12345678"
FILES_STANDARD = "abcdefgh"
FILES_BANK1 = "wx"
FILES_BANK2 = "yz"
FILES_BANKS = FILES_BANK1 + FILES_BANK2
ALL_FILES = FILES_STANDARD + FILES_BANKS

# Game state machine
SETUP_BOARD_AND_PLAYERS = 0
PLAYING_GAME = 1

# detect whether we're on windows or linux
STOCKFISH_PATHS = {
    'windows': '..\\stockfish-16-windows\\stockfish-windows-x86-64-avx2.exe',
    'linux': '/home/chess/new-magnetic-chess/stockfish-16-linux/src/stockfish'
}
os_name = os.name
if (os_name == 'nt'): # Windows
    current_os = 'windows'
else:
    current_os = 'linux'
STOCKFISH_PATH = STOCKFISH_PATHS[current_os]
TEXEL_PATH = '/home/chess/new-magnetic-chess/texel-11-linux/build/texel'

# Bank piece types
BANK_PIECE_TYPES = {
    'w8': 'P',  'x8': 'Q',  'y8': 'q',  'z8': 'p',
    'w7': 'P',  'x7': 'Q',  'y7': 'q',  'z7': 'p',
    'w6': 'P',  'x6': 'R',  'y6': 'r',  'z6': 'p',
    'w5': 'P',  'x5': 'R',  'y5': 'r',  'z5': 'p',
    'w4': 'P',  'x4': 'B',  'y4': 'b',  'z4': 'p',
    'w3': 'P',  'x3': 'B',  'y3': 'b',  'z3': 'p',
    'w2': 'P',  'x2': 'N',  'y2': 'n',  'z2': 'p',
    'w1': 'P',  'x1': 'N',  'y1': 'n',  'z1': 'p',
}

# Bank fill order
BANK_FILL_ORDER = {
    'P': ['w8', 'w7', 'w6', 'w5', 'w4', 'w3', 'w2', 'w1'],
    'Q': ['x8', 'x7'],
    'R': ['x6', 'x5'],
    'B': ['x4', 'x3'],
    'N': ['x2', 'x1'],
    'p': ['z8', 'z7', 'z6', 'z5', 'z4', 'z3', 'z2', 'z1'],
    'q': ['y8', 'y7'],
    'r': ['y6', 'y5'],
    'b': ['y4', 'y3'],
    'n': ['y2', 'y1']
}

NUM_PIECES = {
    'P': 8, 'Q': 2, 'R': 2, 'B': 2, 'N': 2, 'K': 1,
    'p': 8, 'q': 2, 'r': 2, 'b': 2, 'n': 2, 'k': 1
}

# Physical moves for each castling move
WHITE_KINGSIDE_CASTLE_PHYSICAL = {'e1': False, 'f1': True, 'g1': True, 'h1': False}
WHITE_QUEENSIDE_CASTLE_PHYSICAL = {'e1': False, 'd1': True, 'c1': True, 'a1': False}
BLACK_KINGSIDE_CASTLE_PHYSICAL = {'e8': False, 'f8': True, 'g8': True, 'h8': False}
BLACK_QUEENSIDE_CASTLE_PHYSICAL = {'e8': False, 'd8': True, 'c8': True, 'a8': False}

# All possible en passant moves, of the form (pawn_start, pawn_end, captured_pawn)
ALL_EN_PASSANT_PHYSICAL = []
for file in range(len(FILES_STANDARD)):
    if (file != 0):
        ALL_EN_PASSANT_PHYSICAL.append((FILES_STANDARD[file-1] + '5', FILES_STANDARD[file] + '6', FILES_STANDARD[file] + '5'))
        ALL_EN_PASSANT_PHYSICAL.append((FILES_STANDARD[file-1] + '4', FILES_STANDARD[file] + '3', FILES_STANDARD[file] + '4'))
    if (file != len(FILES_STANDARD)-1):
        ALL_EN_PASSANT_PHYSICAL.append((FILES_STANDARD[file+1] + '5', FILES_STANDARD[file] + '6', FILES_STANDARD[file] + '5'))
        ALL_EN_PASSANT_PHYSICAL.append((FILES_STANDARD[file+1] + '4', FILES_STANDARD[file] + '3', FILES_STANDARD[file] + '4'))

class ChessInterface:
    def __init__(self, enableSound=True, audioObject=None):
        self.state = SETUP_BOARD_AND_PLAYERS
        self.stockfish = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) # Use Stockfish as our engine.
        if (current_os == 'linux'):
            self.texel = chess.engine.SimpleEngine.popen_uci(TEXEL_PATH) # Use Texel.
        self.board = chess.Board()
        self.physicalBoard = PhysicalBoard()
        self.stackLengthAfterMove = [] # Since moves can take multiple steps, we keep track of the final length of the stack after the move is complete 
        self.physicalMoveStack = []
        self.reedSwitchStateChanges = []
        self.lastReedSwitchUpdate = time.time()
        self.lastMoveTime = time.time()
        self.movesSinceLastHome = 0
        self.gameEnded = False
        self.whiteElo = None
        self.blackElo = -625

        self.enableSound = enableSound
        self.audio = None
        if (enableSound):
            if (audioObject != None):
                self.audio = audioObject
            else:
                self.audio = Audio()
            
            self.audio.playSound("boot")

    def getEngineMove(self, elo=None):
        # If elo is None, get the best move form stockfish, otherwise, set the Texel ELO to the given value
        # Return the best move
        if (elo == None):
            return self.stockfish.play(self.board, chess.engine.Limit(time=0.2)).move
        else:
            self.texel.configure({"UCI_LimitStrength": True, "UCI_Elo": elo})
            return self.texel.play(self.board, chess.engine.Limit(time=0.2)).move
    
    def getEval(self):
        # Get the evaluation of the current board position from white's perspective
        # Examples: "0.0", "+0.2", "+71.2", "+M3", "-M2"
        info = self.stockfish.analyse(self.board, chess.engine.Limit(time=0.2))
        # Check for mate
        if (info["score"].white().mate() != None):
            if (info["score"].white().mate() >= 0):
                return "+M" + str(info["score"].white().mate())
            else:
                return "-M" + str(-info["score"].white().mate())
        else:
            return str(round(info["score"].white().score() / 100.0, 1))
    
    def __allFileRankSquaresAtTaxicabDistance(self, startFileRank, distance):
        # Get all (existing) squares at a given taxicab distance from a given square. Distance must be greater than 0.
        """
        VISUAL EXAMPLE: All squares of distance 2 from start O inside board dimensions. (board smaller for simplicity)
           6 [ ] [ ] [ ] [*] [ ]
           5 [ ] [ ] [*] [ ] [*]
           4 [ ] [*] [ ] [O] [ ]
         ^ 3 [ ] [ ] [*] [ ] [*]
         | 2 [ ] [ ] [ ] [*] [ ]
         | 1 [ ] [ ] [ ] [ ] [ ]
         |    0   1   2   3   4
        rank   file----->

        """
        if (PhysicalBoard.checkInBounds(startFileRank, printErrors=True) == False):
            return []
        if (distance <= 0):
            print("Distance must be greater than 0.")
            return []
        
        (originFile, originRank) = startFileRank
        right = (originFile + distance, originRank)
        left = (originFile - distance, originRank)
        up = (originFile, originRank + distance)
        down = (originFile, originRank - distance)

        fileRankSquares = []
        # Left square to up square
        fileRank = left
        while (fileRank != up):
            if PhysicalBoard.checkInBounds(fileRank, printErrors=False): # Out of bounds is fine here, we just don't return it
                fileRankSquares.append(fileRank)
            fileRank = (fileRank[0] + 1, fileRank[1] + 1) # Move up and to the right until we reach the up square
        
        # Up square to right square
        while (fileRank != right):
            if PhysicalBoard.checkInBounds(fileRank, printErrors=False):
                fileRankSquares.append(fileRank)
            fileRank = (fileRank[0] + 1, fileRank[1] - 1) # Move down and to the right until we reach the right square
        
        # Right square to down square
        while (fileRank != down):
            if PhysicalBoard.checkInBounds(fileRank, printErrors=False):
                fileRankSquares.append(fileRank)
            fileRank = (fileRank[0] - 1, fileRank[1] - 1) # Move down and to the left until we reach the down square
        
        # Down square to left square
        while (fileRank != left):
            if PhysicalBoard.checkInBounds(fileRank, printErrors=False):
                fileRankSquares.append(fileRank)
            fileRank = (fileRank[0] - 1, fileRank[1] + 1) # Move up and to the left until we reach the left square
        
        return fileRankSquares

    def allSquaresSortedByTaxicabDistance(self, startSquare):
        # Yields a list of all squares ('a1') sorted by taxicab distance from the start square
        
        distance = 1
        while (distance <= 18): # All squares are within 18 squares (taxicab distance) of every other square, so that's our hard cap on distance
            fileRankSquares = self.__allFileRankSquaresAtTaxicabDistance(PhysicalBoard.getFileRankCoords(startSquare), distance)
            if (len(fileRankSquares) == 0): # No squares at this distance, so we're done. No configuration will lead to more squares at a greater distance.
                break
            for fileRank in fileRankSquares:
                yield PhysicalBoard.getSquareFromFileRank(fileRank)
            distance += 1

    def __getEmptyBankSquare(self, color, type):
        # Loop through the bank fill order to find the first empty square of the given type
        symbol = chess.Piece(type, color).symbol()
        position = ChessInterface.getBoardPositionDict(self.board)
        for square in BANK_FILL_ORDER[symbol]:
            if (position[square] == None):
                return square
        return None
    
    def __getFilledBankSquare(self, color, type):
        # Loop backwards through the bank fill order to find the most recently filled square of the given type
        symbol = chess.Piece(type, color).symbol()
        position = ChessInterface.getBoardPositionDict(self.board)
        for square in reversed(BANK_FILL_ORDER[symbol]):
            if (position[square] != None):
                return square
        return None

    def __movePhysical(self, extendedMove, sendCommand=True, useStack=True):
        # Move the piece on the physical board
        if (useStack):
            self.physicalMoveStack.append(extendedMove) # Push the move to the move stack

        # Get start and end
        start = extendedMove[0][0:2]
        end = extendedMove[0][2:4]
        direct = extendedMove[1]

        print("MOVING PIECE: " + start + " -> " + end + " (direct: " + str(direct) + ")")
        if (sendCommand):
            self.physicalBoard.movePiece(start, end, direct=direct)
            self.movesSinceLastHome += 1
    
    def __undoPhysical(self, sendCommand=True, useStack=True):
        # Undo the move on the physical board
        if (useStack):
            move = self.physicalMoveStack.pop()
        if (sendCommand):
            self.physicalBoard.movePiece(move[0][2:4], move[0][0:2], direct=move[1])
            self.movesSinceLastHome += 1
    
    def undoLastMove(self, sendCommands=True):
        # Undo the last move on the virtual board
        self.board.pop()
        
        # Undo the last move on the physical board
        self.stackLengthAfterMove.pop() # Remove last item without looking at it (unneeded)
        newLength = self.stackLengthAfterMove[-1] if len(self.stackLengthAfterMove) > 0 else 0 # Get the length of the stack after the move

        # Remove physical moves until our stack length is correct
        while (len(self.physicalMoveStack) > newLength):
            self.__undoPhysical(sendCommand=sendCommands)

    def move(self, move, checkLegal=True, sendCommands=True):
        if (checkLegal and move not in self.board.legal_moves):
            print("Illegal move: " + move.uci() + ".")
            return False
        
        pieceType = self.board.piece_type_at(move.from_square)
        start = chess.square_name(move.from_square)
        end = chess.square_name(move.to_square)

        opposite = {chess.WHITE: chess.BLACK, chess.BLACK: chess.WHITE}
        opponent = opposite[self.board.turn]

        # Includes moving captured pieces to bank and castling
        physicalMoves = []

        # Handle castling
        if (self.board.is_castling(move=move)):
            # Move the king first, directly
            physicalMoves.append((start + end, True))
            # Move the rook
            if (end == "c1"):
                physicalMoves.append(("a1d1", False))
            elif (end == "g1"):
                physicalMoves.append(("h1f1", False))
            elif (end == "c8"):
                physicalMoves.append(("a8d8", False))
            elif (end == "g8"):
                physicalMoves.append(("h8f8", False))
            
            if self.enableSound:
                self.audio.playSound("castle")
        
        elif (self.board.is_en_passant(move=move)):
            capturedSquare = end[0] + start[1] # Get opponent's pawn's position, which should be on the new file but the same rank.
            bankSquare = self.__getEmptyBankSquare(opponent, chess.PAWN)

            if (start is not None and end is not None and capturedSquare is not None and bankSquare is not None):
                physicalMoves.append((start + end, True)) # Move our pawn directly
                physicalMoves.append((capturedSquare + bankSquare, False)) # Move opponent's pawn to bank
            else:
                print("Error: could not find required squares for move " + move.uci() + ".")
                return False

            if self.enableSound:
                self.audio.playSound("capture")
        
        elif (move.promotion is not None): # Pawn Promotion
            promotedBankSquare = self.__getFilledBankSquare(self.board.turn, move.promotion)
            removedBankSquare = self.__getEmptyBankSquare(self.board.turn, chess.PAWN)

            if (start is not None and end is not None and promotedBankSquare is not None and removedBankSquare is not None):
                physicalMoves.append((promotedBankSquare + end, False)) # Move the promoted piece from the bank to the board
                physicalMoves.append((start + removedBankSquare, False)) # Move our pawn back to our bank
            else:
                print("Error: could not find required squares for move " + move.uci() + ".")
                return False

            if self.enableSound:
                self.audio.playSound("promote")

        elif (self.board.is_capture(move=move)): # Normal capture
            capturedPiece = self.board.piece_at(move.to_square)
            capturedType = capturedPiece.piece_type
            bankSquare = self.__getEmptyBankSquare(opponent, capturedType)

            if (start is not None and end is not None and bankSquare is not None):
                physicalMoves.append((end + bankSquare, False)) # Move opponent's piece to bank
                physicalMoves.append((start + end, pieceType != chess.KNIGHT)) # Move our piece directly if it's not a knight
            else:
                print("Error: could not find required squares for move " + move.uci() + ".")
                return False

            if self.enableSound:
                self.audio.playSound("capture")

        else: # Normal move
            physicalMoves.append((start + end, pieceType != chess.KNIGHT))

            if self.enableSound:
                self.audio.playSound("move")
        
        # Move the piece on the virtual board
        self.board.push(move)

        if (self.enableSound):
            if (self.board.is_check()):
                self.audio.playSound("check")

        # Move the piece on the physical board
        for physicalMove in physicalMoves:
            self.__movePhysical(physicalMove, sendCommand=sendCommands)
        self.stackLengthAfterMove.append(len(self.physicalMoveStack))
        return True
    
    def checkDirectPath(self, start, end):
        # Check if there is a direct, empty path between two squares. DOES NOT CHECK START AND END SQUARES.
        (startFile, startRank) = PhysicalBoard.getFileRankCoords(start)
        (endFile, endRank) = PhysicalBoard.getFileRankCoords(end)

        fileDifference = abs(endFile - startFile)
        rankDifference = abs(endRank - startRank)
        if (fileDifference == 0 or rankDifference == 0 or fileDifference == rankDifference):
            if (fileDifference <= 1 and rankDifference <= 1):
                return True
            else:
                intermediateSquaresFileRank = []
                minFile = min(startFile, endFile)
                maxFile = max(startFile, endFile)
                minRank = min(startRank, endRank)
                maxRank = max(startRank, endRank)
                
                if (fileDifference == 0):
                    for rank in range(minRank+1, maxRank):
                        intermediateSquaresFileRank.append((startFile, rank))
                elif (rankDifference == 0):
                    for file in range(minFile+1, maxFile):
                        intermediateSquaresFileRank.append((file, startRank))
                else:
                    # Which diagonal line are we on? / or \
                    if ((startFile < endFile and startRank < endRank) or (startFile > endFile and startRank > endRank)): # /
                        reverseRankList = False
                    else: # \
                        reverseRankList = True
                    
                    fileRange = list(range(minFile+1, maxFile))
                    rankRange = list(range(minRank+1, maxRank))
                    if (reverseRankList):
                        rankRange.reverse()
                    
                    for i in range(len(fileRange)):
                        intermediateSquaresFileRank.append((fileRange[i], rankRange[i]))

                for (file, rank) in intermediateSquaresFileRank:
                    # Convert back to square name
                    if (0 <= file <= 7 and 1 <= rank <= 8):
                        square = FILES_STANDARD[file] + RANKS[rank-1]
                        if (self.board.piece_at(chess.SQUARE_NAMES.index(square)) is not None):
                            print(intermediateSquaresFileRank)
                            print("Piece in the way: " + square)
                            return False
                    else:
                        return False # Outside standard board
                
                return True # No pieces in the way
        else:
            return False
    
    def updatePhysicalMoveInProgress(self):
        # Update the physical move in progress
        modifiedReedSwitches = self.physicalBoard.getModifiedReedSwitches()

        for square, state in modifiedReedSwitches:
            self.reedSwitchStateChanges.append((square, state))

    def getMoveFromReedSwitches(self, allowIllegalMoves=False):
        # Get the move from the reed switches. Returns None if no move is detected.
        self.updatePhysicalMoveInProgress()
        
        originalStates = {}
        tempCurrentState = {}

        finalStateChanges = {}
        finallyUnmodified = {} # Squares that changed, then changed back to their original state (captured piece?)
        order = [] # Order of squares these updates happened
        increasedTotal = 0 # +1 for each square filled, -1 for each square emptied, should be 0 after a complete move

        # Populate the lists above
        for (square, state) in self.reedSwitchStateChanges:
            tempCurrentState[square] = state
            increasedTotal += 1 if state else -1
            if (square not in originalStates): # Get original state of square if we haven't seen it yet
                originalStates[square] = not state
            
            if (square not in order): # Get correct order of modified squares
                order.append(square)
            else:
                order.remove(square) # Remove from the list if it's already in there
                order.append(square)
        
        for square in order:
            if (tempCurrentState[square] == originalStates[square]):
                finallyUnmodified[square] = tempCurrentState[square]
            else:
                finalStateChanges[square] = tempCurrentState[square]
        
        # Simple check for incomplete move (doesn't catch all cases)
        if (increasedTotal != 0): # Pieces added or removed from the board (including bank)
            return None
        
        # Count bank squares filled and removed
        bankSquaresFilled = 0
        bankSquaresRemoved = 0
        for (square, state) in finalStateChanges.items():
            if (square[0] in FILES_BANKS):
                if (state == True):
                    bankSquaresFilled += 1
                else:
                    bankSquaresRemoved += 1
        allMovesInStandardBoard = bankSquaresFilled == 0 and bankSquaresRemoved == 0

        physicalMoves = []

        # ALL MOVES FULLY WITHIN STANDARD BOARD:
        if (allMovesInStandardBoard):
            # CASTLE: For a castle, in any order, the king must make a specific move, and either rook must make a specific move.
            if (len(finalStateChanges) == 4):
                if (finalStateChanges == WHITE_KINGSIDE_CASTLE_PHYSICAL):
                    physicalMoves.append(('e1g1', True))
                    physicalMoves.append(('h1f1', False))
                elif (finalStateChanges == WHITE_QUEENSIDE_CASTLE_PHYSICAL):
                    physicalMoves.append(('e1c1', True))
                    physicalMoves.append(('a1d1', False))
                elif (finalStateChanges == BLACK_KINGSIDE_CASTLE_PHYSICAL):
                    physicalMoves.append(('e8g8', True))
                    physicalMoves.append(('h8f8', False))
                elif (finalStateChanges == BLACK_QUEENSIDE_CASTLE_PHYSICAL):
                    physicalMoves.append(('e8c8', True))
                    physicalMoves.append(('a8d8', False))
            # NORMAL: For a normal move, the piece must move from one square to another, both on the standard board.
            elif (len(finalStateChanges) == 2):
                start = 'a1'
                end = 'a1'
                # find the start square (piece removed)
                for square, state in finallyUnmodified.items():
                    if (state == False):
                        start = square
                    if (state == True):
                        end = square
                
                # Check for direct path
                isDirectPath = self.checkDirectPath(start, end)
                physicalMoves.append((start + end, isDirectPath))

        # ALL MOVES INVOLVING BANK:
        else:
            # ONE BANK SQUARE FILLED:
            if (bankSquaresFilled == 1):
                # ONE BANK SQUARE FILLED, ONE BANK SQUARE EMPTIED
                if (bankSquaresRemoved == 1):
                    # PROMOTION: For a promotion, in any order, the pawn must move to the bank, and the promoted piece must move to the board.
                    if (len(finalStateChanges) == 4):
                        pawnStart = None
                        promotionSquare = None
                        filledBank = None
                        emptiedBank = None

                        for (square, state) in finallyUnmodified.items():
                            if ((square[1] == '7' or square[1] == '2') and state == False):
                                pawnStart = square
                            if ((square[1] == '8' or square[1] == '1') and state == True):
                                promotionSquare = square
                            if (square[0] in FILES_BANKS and state == True):
                                filledBank = square
                            if (square[0] in FILES_BANKS and state == False):
                                emptiedBank = square
                        
                        if (pawnStart != None and promotionSquare != None and filledBank != None and emptiedBank != None):
                            physicalMoves.append((filledBank + promotionSquare, False))
                            physicalMoves.append((pawnStart + emptiedBank, False))
                
                else:
                    # EN PASSANT: For an en passant, in any order, the pawn must capture an empty square, and the opponent's pawn must move to the bank.
                    if (len(finalStateChanges) == 4):
                        for (pawn_start, pawn_end, captured_pawn) in ALL_EN_PASSANT_PHYSICAL:
                            if (pawn_start in finalStateChanges and pawn_end in finalStateChanges and captured_pawn in finalStateChanges):
                                if (finalStateChanges[pawn_start] == False and finalStateChanges[pawn_end] == True and finalStateChanges[captured_pawn] == False):
                                    # Get the bank square from finalStateChanges
                                    bankSquare = 'a1'
                                    for square, state in finalStateChanges.items():
                                        if (square[0] in FILES_BANKS):
                                            bankSquare = square
                                    
                                    physicalMoves.append((pawn_start + pawn_end, True))
                                    physicalMoves.append((captured_pawn + bankSquare, False))
                    
                    # CAPTURE: For a capture, the capturing piece must move to the captured piece's square, and the captured piece must move to the bank.
                    # Alternatively, the capturing piece might dissapear and the captured piece might appear in the bank. In that case, use legal moves to find out what happened.
                    if (len(finalStateChanges) == 2):
                        start = 'a1'
                        bank = 'w1'
                        for square, state in finalStateChanges.items():
                            if (state == False):
                                start = square
                            if (state == True):
                                bank = square
                        
                        capturingPiece = self.board.piece_at(chess.SQUARE_NAMES.index(start)).symbol()
                        capturedPiece = BANK_PIECE_TYPES[bank]

                        # Get legal captures that begin with the start square and capture the captured piece type
                        legalMoves = self.board.legal_moves
                        legalCapturesFromStart = []
                        for move in legalMoves:
                            if (move.from_square == chess.SQUARE_NAMES.index(start) and self.board.piece_at(move.to_square).symbol() == capturedPiece):
                                legalCapturesFromStart.append(move)
                        
                        mostLikelyMove = None
                        if (len(legalCapturesFromStart) >= 1): # Multiple legal captures matching these piece types, use unmodified squares as a tiebreaker
                            for move in legalCapturesFromStart:
                                toSquareName = chess.square_name(move.to_square)
                                if (toSquareName in finallyUnmodified):
                                    if (finallyUnmodified[toSquareName] == True): # The square was briefly unfilled, so it's likely the captured piece
                                        mostLikelyMove = move
                                        break
                            if (mostLikelyMove == None): # No squares were briefly unfilled, so just pick arbitrarily
                                mostLikelyMove = legalCapturesFromStart[0]
                        elif (len(legalCapturesFromStart) == 1):
                            mostLikelyMove = legalCapturesFromStart[0]
                        
                        if (mostLikelyMove != None):
                            physicalMoves.append((chess.square_name(mostLikelyMove.to_square) + bank, False))
                            physicalMoves.append((start + chess.square_name(mostLikelyMove.to_square), capturingPiece != chess.KNIGHT))

    @staticmethod
    def getBoardPositionDict(board, printErrors=True):
        position = {}
        missing_piece_counts = NUM_PIECES.copy()

        for file in FILES_STANDARD:
            for rank in RANKS:
                piece = board.piece_at(chess.SQUARE_NAMES.index(file+rank))
                symbol = piece.symbol() if piece != None else None
                position[file+rank] = symbol
                if (symbol != None):
                    missing_piece_counts[symbol] -= 1
        
        for piece_symbol in BANK_FILL_ORDER:
            if (missing_piece_counts[piece_symbol] < 0): # Check for too many pieces
                if (printErrors):
                    print("Extra " + str(-missing_piece_counts[piece_symbol]) + "*" + piece_symbol + " found on the board. Cannot load position.")
                return None
            
            for square in BANK_FILL_ORDER[piece_symbol]:
                if (missing_piece_counts[piece_symbol] > 0):
                    position[square] = piece_symbol
                    missing_piece_counts[piece_symbol] -= 1
                else:
                    position[square] = None
            
            if (missing_piece_counts[piece_symbol] > 0): # Pieces unable to be put in bank
                if (printErrors):
                    print("Board missing " + str(missing_piece_counts[piece_symbol]) + "*" + piece_symbol + " which could not be placed into bank.")
                return None
        
        return position

    def physicalMovesPositionToPosition(self, oldPosition, newPosition):
        """
        Algorithm:

        While there are unresolved start squares:
            Find nearest unresolved start square to current square
            Find nearest unfilled target for it

            If all targets are filled:
                Find nearest filled target to current square.
                Move that target to the nearest empty square.
            
            Move the piece to the nearest unfilled target.
            
        """

        # Convert a position of physical moves to a position of pieces
        position = oldPosition.copy()
        newPositionByPiece = { # For each piece, get target squares
            'P': [], 'Q': [], 'R': [], 'B': [], 'N': [], 'K': [],
            'p': [], 'q': [], 'r': [], 'b': [], 'n': [], 'k': []
        }
        for square in newPosition.keys():
            piece = newPosition[square]
            if (piece != None):
                newPositionByPiece[piece].append(square)
        
        unresolvedStartSquares = []
        for square, piece in position.items(): 
            if (piece != None):
                if (square in newPositionByPiece[piece]): # Piece is in the correct square
                    position[square] = None
                else: # Piece is in the wrong square
                    unresolvedStartSquares.append(square)
        
        # Start at the closest location to the magnet
        currentSquare = PhysicalBoard.getSquareFromFileRank(self.physicalBoard.finalDestinationFileRank)
        physicalMoves = []

        # While there are unresolved start squares:
        while (len(unresolvedStartSquares) > 0):
            # Find nearest unresolved start square to current square
            nearestUnresolvedStartSquare = None
            minDistance = 9999
            for square in unresolvedStartSquares:
                distance = PhysicalBoard.taxicabDistance(currentSquare, square)
                if (nearestUnresolvedStartSquare == None or distance < minDistance):
                    nearestUnresolvedStartSquare = square
                    minDistance = distance
            
            # Error handling, make sure there is at least one target
            if (len(newPositionByPiece[position[nearestUnresolvedStartSquare]]) == 0):
                print("No target squares for piece " + position[nearestUnresolvedStartSquare] + "at square " + nearestUnresolvedStartSquare + ".")
                return None

            # Find nearest unfilled target for piece at current squares
            nearestUnfilledTarget = None
            nearestTarget = None
            minDistanceToUnfilledTarget = 9999
            minDistanceToTarget = 9999
            for target in newPositionByPiece[position[nearestUnresolvedStartSquare]]:
                distance = PhysicalBoard.taxicabDistance(nearestUnresolvedStartSquare, target)
                if (nearestTarget == None or distance < minDistanceToTarget): # Any target
                    nearestTarget = target
                    minDistanceToTarget = distance
                if (position[target] == None and (nearestUnfilledTarget == None or distance < minDistanceToUnfilledTarget)): # Unfilled target
                    nearestUnfilledTarget = target
                    minDistanceToUnfilledTarget = distance
            
            # If all targets are filled:
            if (nearestUnfilledTarget == None):
                # Use nearest filled target to current square
                nearestFilledTarget = nearestTarget

                # Move that target to the nearest empty square to it.
                nearestEmptySquare = None
                for square in self.allSquaresSortedByTaxicabDistance(nearestFilledTarget):
                    if (position[square] == None):
                        nearestEmptySquare = square
                        break
                
                if (nearestEmptySquare == None):
                    print("No empty squares near filled target " + nearestFilledTarget)
                    return None
            
                # Move the piece to the nearest empty square to it
                position[nearestEmptySquare] = position[nearestFilledTarget]
                position[nearestFilledTarget] = None

                # Update unresolved start squares, to ensure the piece we just moved out of the way gets where it needs to go
                if (nearestFilledTarget in unresolvedStartSquares):
                    unresolvedStartSquares.remove(nearestFilledTarget)
                    unresolvedStartSquares.append(nearestEmptySquare)

                # Update nearestUnfilledTarget
                nearestUnfilledTarget = nearestEmptySquare
                
                physicalMoves.append((nearestFilledTarget + nearestEmptySquare, False)) # Physical move
            
            # Move the piece to the nearest unfilled target
            position[nearestUnfilledTarget] = position[nearestUnresolvedStartSquare]
            position[nearestUnresolvedStartSquare] = None

            # Update unresolved start squares
            unresolvedStartSquares.remove(nearestUnresolvedStartSquare)

            physicalMoves.append((nearestUnresolvedStartSquare + nearestUnfilledTarget, False)) # Physical move
        
        return physicalMoves
    
    def setBoardFEN(self, fen, sendCommands=True, errorCheckUsingReedSwitches=True):
        # Get current position from virtual board
        currentPosition = ChessInterface.getBoardPositionDict(self.board)

        if errorCheckUsingReedSwitches:
            # Ensure the physical board matches the virtual board (reed switches)
            missingSquares = []
            extraSquares = []
            for square in currentPosition.keys():
                if (currentPosition[square] == None): # No piece, reed switch should be off
                    if (self.physicalBoard.reedSwitches[square] == True):
                        extraSquares.append(square)
                else: # Piece, reed switch should be on
                    if (self.physicalBoard.reedSwitches[square] == False):
                        missingSquares.append(square)
            
            if (len(missingSquares) > len(extraSquares)):
                print("Board is missing pieces!")
                return
            
            if (len(missingSquares) + len(extraSquares) > 0):
                print("Board position inconsistent with reed switches.")
                if (len(missingSquares) + len(extraSquares) > 2):
                    print("More than 2 squares are inconsistent, cannot automatically fix. Please reset to the starting position manually.")
                    return
            
            # Basic error correction for one missing and one extra square
            if (len(missingSquares) == 1 and len(extraSquares) == 1):
                # In our virtual position, move the piece from the extra square to the missing square
                currentPosition[missingSquares[0]] = currentPosition[extraSquares[0]]
                currentPosition[extraSquares[0]] = None

        self.board.set_fen(fen) # Set the virtual board position
        newPosition = ChessInterface.getBoardPositionDict(self.board)
        physicalMoves = self.physicalMovesPositionToPosition(currentPosition, newPosition) # Physical moves to set the board position
        
        # Make the physical moves
        for move in physicalMoves:
            self.__movePhysical(move, sendCommand=sendCommands, useStack=False)
    
    def resetBoard(self, sendCommands=True, errorCheckUsingReedSwitches=True):
        # Reset the board to the starting position
        self.physicalMoveStack = []
        self.stackLengthAfterMove = []
        if (self.board.fen() == chess.STARTING_FEN): # Already at the starting position
            return
        
        self.setBoardFEN(chess.STARTING_FEN, sendCommands=sendCommands, errorCheckUsingReedSwitches=errorCheckUsingReedSwitches)
        
    def handleArcadeButtons(self, isInGame=False):
        # TODO: Caleb - Handle arcade buttons
        pass

    def printBoard(self):
        fullPosition = ChessInterface.getBoardPositionDict(self.board)
        for rank in reversed(RANKS):
            for file in FILES_BANKS:
                piece = fullPosition[file+rank]
                if (piece == None):
                    print(".", end=" ")
                else:
                    print(piece, end=" ")
            print(" ", end=" ")
            for file in FILES_STANDARD:
                piece = fullPosition[file+rank]
                if (piece == None):
                    print(".", end=" ")
                else:
                    print(piece, end=" ")
            print()
        print("Evaluation: " + self.getEval())

    def update(self, sendCommands=True):
        # Update physical board
        self.physicalBoard.update()

        # State machine
        if (self.state == SETUP_BOARD_AND_PLAYERS):
            self.resetBoard(sendCommands=sendCommands, errorCheckUsingReedSwitches=False)
            
            # Setup board and players
            self.handleArcadeButtons(isInGame=False)
            if (not self.physicalBoard.isAllCommandsFinished()):
                self.state = PLAYING_GAME # TODO: DEBUG - REMOVE THIS LINE
                self.gameEnded = False
        elif (self.state == PLAYING_GAME):
            # Play the game
            # self.updatePhysicalMoveInProgress()

            """
            # Handle moves
            move = self.getMoveFromReedSwitches() # TODO: Don't do this if no reed switches have changed
            if (move != None):
                currentTime = time.time()
                self.lastReedSwitchUpdate = currentTime
                # Wait to ensure validity - e.g. someone sliding a bishop doesn't trigger a move until they leave it at the end square
                if (currentTime - self.lastReedSwitchUpdate > MOVE_VALIDITY_THRESHOLD):
                    self.move(move, sendCommands=False)
            """

            # Stockfish move
            elo = self.whiteElo if self.board.turn == chess.WHITE else self.blackElo
            move = self.getEngineMove(elo=elo)
            if (move != None and move.uci() != "0000"):
                if ((self.physicalBoard.isAllCommandsFinished() and time.time() - self.physicalBoard.firstAvailableTime > COMPUTER_MOVE_DELAY) or sendCommands == False):
                    self.printBoard()
                    print("Engine move: " + move.uci())
                    self.physicalBoard.firstAvailableTime += COMPUTER_MOVE_DELAY # Prevent moving again before physical board realizes there was a move
                    success = self.move(move, sendCommands=sendCommands)
                    if (not success):
                        legalMoves = self.board.legal_moves
                        print("Trying all legal moves to see if they are possible")
                        while legalMoves is not None and legalMoves != []:
                            # Choose a random legal move index
                            moveIndex = random.randint(0, len(legalMoves) - 1)
                            legalMove = legalMoves.pop(moveIndex)
                            success = self.move(legalMove, sendCommands=sendCommands)
                            if (success):
                                break
                    if (not success):
                        print("Engine move failed (not possible to do with piece bank).")
                        return True
            
            # Check for game end
            if (self.board.is_game_over()):
                if (not self.gameEnded):
                    self.gameEnded = True

                    self.printBoard()
                    result = "Checkmate" if self.board.is_checkmate() else "Stalemate" if self.board.is_stalemate() else "Non-stalemate draw"
                    print("Game over by " + result)

                    if (self.enableSound):
                        self.audio.playSound("gameend")

                    self.physicalBoard.enqueueCommand('HPX0000Y0000')
                
                # Wait for the arduino to finish
                if (self.physicalBoard.isAllCommandsFinished()):
                    self.state = SETUP_BOARD_AND_PLAYERS
                    return True
    
    def setWhiteElo(self, elo):
        self.whiteElo = elo
    
    def setBlackElo(self, elo):
        self.blackElo = elo
    
    def goTo(self, x, y, magnetUp=False, home=True):
        # Debugging function to move the physical board to a specific location
        homeCommand = 'HPX0000Y0000'
        command = self.physicalBoard.buildCommand(x, y, magnetUp, False)
        if (home):
            self.physicalBoard.enqueueCommand(homeCommand)
        self.physicalBoard.enqueueCommand(command)
        while not self.physicalBoard.isAllCommandsFinished():
            self.physicalBoard.update()
    
    def goToSquare(self, square, magnetUp=False, home=True):
        # Debugging function to move the physical board to a specific square
        fileRank = self.physicalBoard.getFileRankCoords(square)
        (x, y) = self.physicalBoard.getXYFromFileRank(fileRank)
        self.goTo(x, y, magnetUp=magnetUp, home=home)
    
    def loop(self, sendCommands=True):
        # Main loop
        try:
            gameOver = False
            while not gameOver:
                gameOver = self.update(sendCommands=sendCommands)
        except KeyboardInterrupt:
            self.physicalBoard.close()
            if (self.enableSound):
                self.audio.close()
            if (self.stockfish != None):
                self.stockfish.quit()
            if (self.texel != None):
                self.texel.quit()
            print("Keyboard interrupt. Exiting.")
            return
        
