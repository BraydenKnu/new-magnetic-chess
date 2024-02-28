"""
CHESS INTERFACE

Interface between the user, stockfish, and the PhysicalBoard class.


COORDINATE SYSTEM
    - Bank1    Main Board     Bank2
    - _____ _________________ _____
    8 |_|_| |_|_|_|_|_|_|_|_| |_|_| 
    7 |_|_| |_|_|_|_|_|_|_|_| |_|_|
    6 |_|_| |_|_|_|_|_|_|_|_| |_|_|
    5 |_|_| |_|_|_|_|_|_|_|_| |_|_|
    4 |_|_| |_|_|_|_|_|_|_|_| |_|_|
y   3 |_|_| |_|_|_|_|_|_|_|_| |_|_|
^   2 |_|_| |_|_|_|_|_|_|_|_| |_|_|
|   1 |_|_| |_|_|_|_|_|_|_|_| |_|_|
|      w x   a b c d e f g h   y z
|     -3-2 _ 0 1 2 3 4 5 6 7 _ 9 10 (file)
+-----> x
^
(0, 0)

BANK PIECES
    -   Bank1        Bank2
    - +---+---+     +---+---+
    8 | p | q |     | Q | P |
    - +---+---+     +---+---+
    7 | p | q |     | Q | P |
    - +---+---+     +---+---+
    6 | p | r |     | R | P |
    - +---+---+     +---+---+
    5 | p | r |     | R | P |
    - +---+---+     +---+---+
    4 | p | b |     | B | P |
    - +---+---+     +---+---+
    3 | p | b |     | B | P |
    - +---+---+     +---+---+
    2 | p | n |     | N | P |
    - +---+---+     +---+---+
    1 | p | n |     | N | P |
    - +---+---+     +---+---+
        w   x         y   z
"""

# Imports
import os
from stockfish import Stockfish # (pip install stockfish) Documentation: https://pypi.org/project/stockfish/
import chess                    # (pip install python-chess) Documentation: https://python-chess.readthedocs.io/en/latest/
from PhysicalBoard import PhysicalBoard

# Constants
RANKS = "12345678"
FILES_STANDARD = "abcdefgh"
FILES_BANK1 = "wx"
FILES_BANK2 = "yz"
FILES_BANKS = FILES_BANK1 + FILES_BANK2
ALL_FILES = FILES_STANDARD + FILES_BANKS

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

# Bank piece types
BANK_PIECE_TYPES = {
    'w8': chess.PAWN, 'x8': chess.KNIGHT,'y8': chess.QUEEN, 'z8': chess.PAWN,
    'w7': chess.PAWN, 'x7': chess.KNIGHT,'y7': chess.QUEEN, 'z7': chess.PAWN,
    'w6': chess.PAWN, 'x6': chess.BISHOP,'y6': chess.ROOK,  'z6': chess.PAWN,
    'w5': chess.PAWN, 'x5': chess.BISHOP,'y5': chess.ROOK,  'z5': chess.PAWN,
    'w4': chess.PAWN, 'x4': chess.ROOK,  'y4': chess.BISHOP,'z4': chess.PAWN,
    'w3': chess.PAWN, 'x3': chess.ROOK,  'y3': chess.BISHOP,'z3': chess.PAWN,
    'w2': chess.PAWN, 'x2': chess.QUEEN, 'y2': chess.KNIGHT,'z2': chess.PAWN,
    'w1': chess.PAWN, 'x1': chess.QUEEN, 'y1': chess.KNIGHT,'z1': chess.PAWN
}

# Bank fill order
bankFillOrder = {
    chess.WHITE: {
        chess.PAWN: ['z8', 'z7', 'z6', 'z5', 'z4', 'z3', 'z2', 'z1'],
        chess.QUEEN: ['y8', 'y7'],
        chess.ROOK: ['y6', 'y5'],
        chess.BISHOP: ['y4', 'y3'],
        chess.KNIGHT: ['y2', 'y1']
    },
    chess.BLACK: {
        chess.PAWN: ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8'],
        chess.QUEEN: ['x1', 'x2'],
        chess.ROOK: ['x3', 'x4'],
        chess.BISHOP: ['x5', 'x6'],
        chess.KNIGHT: ['x7', 'x8']
    }
}
filledBankSquares = {} # Keep track of which bank squares are filled
for file in ALL_FILES:
    for rank in RANKS:
        filledBankSquares[file+rank] = False

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
    def __init__(self):
        self.stockfish = Stockfish(STOCKFISH_PATH) # (pip install stockfish) Documentation: https://pypi.org/project/stockfish/
        self.board = chess.Board()
        self.physicalBoard = PhysicalBoard()
        self.stackLengthAfterMove = [] # Since moves can take multiple steps, we keep track of the final length of the stack after the move is complete 
        self.physicalMoveStack = []
        self.reedSwitchStateChanges = []
    
    def __getEmptyBankSquare(self, color, type):
        # Loop through the bank fill order to find the first empty square of the given type
        for square in bankFillOrder[color][type]:
            if (square not in filledBankSquares):
                return square
        return None
    
    def __getFilledBankSquare(self, color, type):
        # Loop backwards through the bank fill order to find the most recently filled square of the given type
        for square in reversed(bankFillOrder[color][type]):
            if (square in filledBankSquares):
                return square
        return None

    def __movePhysical(self, extendedMove, sendCommand=True):
        # Move the piece on the physical board
        self.physicalMoveStack.append(extendedMove) # Push the move to the move stack

        # Get start and end
        start = extendedMove[0][0:2]
        end = extendedMove[0][2:4]
        direct = extendedMove[1]

        if (sendCommand):
            self.physicalBoard.movePiece(start, end, direct=direct)
    
    def __undoPhysical(self, sendCommand=True):
        # Undo the move on the physical board
        move = self.physicalMoveStack.pop()
        if (sendCommand):
            self.physicalBoard.movePiece(move[0][2:4], move[0][0:2], direct=move[1])
    
    def undoLastMove(self, sendCommands=True):
        # Undo the last move on the virtual board
        self.board.pop()
        
        # Undo the last move on the physical board
        self.stackLengthAfterMove.pop()
        newLength = self.stackLengthAfterMove[-1]

        while (len(self.physicalMoveStack) > newLength): # Remove physical moves until our stack length is correct
            self.__undoPhysical(self.physicalMoveStack[-1], sendCommand=sendCommands)

    def move(self, move, checkLegal=True, sendCommands=True):
        if (checkLegal and move not in self.board.legal_moves):
            print("Illegal move: " + move)
            return []
        
        pieceType = self.board.piece_type_at(move.from_square)
        start = chess.square_name(move.from_square)
        end = chess.square_name(move.to_square)

        opposite = {chess.WHITE: chess.BLACK, chess.BLACK: chess.WHITE}
        opponent = opposite[self.board.turn]

        # Includes moving captured pieces to bank and castling
        physicalMoves = []

        # Handle castling
        if (chess.Board.is_castling(move)):
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
        
        elif (chess.Board.is_en_passant(move)):
            capturedSquare = end[0] + start[1] # Get opponent's pawn's position, which should be on the new file but the same rank.
            bankSquare = self.__getEmptyBankSquare(opponent, chess.PAWN)

            physicalMoves.append((start + end, True)) # Move our pawn directly
            physicalMoves.append((capturedSquare + bankSquare, False)) # Move opponent's pawn to bank
        
        elif (move.promotion is not None): # Pawn Promotion
            promotedBankSquare = self.__getFilledBankSquare(self.board.turn, move.promotion)
            removedBankSquare = self.__getEmptyBankSquare(self.board.turn, pieceType)

            physicalMoves.append((promotedBankSquare + end, False)) # Move the promoted piece from the bank to the board
            physicalMoves.append((start + removedBankSquare, True)) # Move our pawn back to our bank

        elif (move.drop is not None): # Capture
            bankSquare = self.__getEmptyBankSquare(opponent, move.drop)

            physicalMoves.append((end + bankSquare, False)) # Move opponent's piece to bank
            physicalMoves.append((start + end, pieceType != chess.KNIGHT)) # Move our piece directly if it's not a knight

        else: # Normal move
            physicalMoves.append((start + end, pieceType != chess.KNIGHT))

        # Move the piece on the virtual board
        self.board.push(chess.Move.from_uci(move))

        # Move the piece on the physical board
        for physicalMove in physicalMoves:
            self.__movePhysical(physicalMove, sendCommand=sendCommands)
        self.stackLengthAfterMove.append(len(self.physicalMoveStack))
    
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
        self.physicalBoard.updateReedSwitches()
        modifiedReedSwitches = self.physicalBoard.getModifiedReedSwitches()

        for square, state in modifiedReedSwitches:
            self.reedSwitchStateChanges.append((square, state))

    def getMoveFromReedSwitches(self):
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
                        
                        capturingPieceType = self.board.piece_type_at(chess.SQUARE_NAMES.index(start))
                        capturedPieceType = BANK_PIECE_TYPES[bank]

                        # Get legal captures that begin with the start square and capture the captured piece type
                        legalMoves = self.board.legal_moves
                        legalCapturesFromStart = []
                        for move in legalMoves:
                            if (move.from_square == chess.SQUARE_NAMES.index(start) and self.board.piece_type_at(move.to_square) == capturedPieceType):
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
                            physicalMoves.append((start + chess.square_name(mostLikelyMove.to_square), capturingPieceType != chess.KNIGHT))

    def update(self):
        # Update physical board
        self.board.update()      
        self.updatePhysicalMoveInProgress()

        move = self.getMoveFromReedSwitches() # TODO: Don't do this if no reed switches have changed
        if (move != None):
            # Wait to ensure validity - e.g. someone sliding a bishop doesn't trigger a move until they leave it at the end square
            # Also ensure a move can be updated as long as the computer has not moved.
            # TODO: Implement wait without delay
            pass
