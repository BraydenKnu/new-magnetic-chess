"""
PHYSICAL BOARD

Controls the motors and the piece magnet by sending commands to the Arduino.


COORDINATE SYSTEM
    - Bank1Bank2   Main Board
    - _________ _________________
    8 |_|_|_|_| |_|_|_|_|_|_|_|_|
    7 |_|_|_|_| |_|_|_|_|_|_|_|_|
    6 |_|_|_|_| |_|_|_|_|_|_|_|_|
    5 |_|_|_|_| |_|_|_|_|_|_|_|_|
    4 |_|_|_|_| |_|_|_|_|_|_|_|_|
    3 |_|_|_|_| |_|_|_|_|_|_|_|_|
    2 |_|_|_|_| |_|_|_|_|_|_|_|_| x
    1 |_|_|_|_| |_|_|_|_|_|_|_|_| ^
       w x y z   a b c d e f g h  |
(file)-5-4-3-2 _ 0 1 2 3 4 5 6 7  |
                          y<------+ (0, 0)

EXTENDED MOVE NOTATION
The board is extended to 12x8 to allow for the movement of the pieces to the banks.
For example, d2z1 is a valid move.

EXTENDED COORDINATE SYSTEM
To support moving pieces to the corners of each square, rank/file coordinates have been converted
to numeirc values, stored as (file, rank) tuples. A1 is at (0, 1).
"""

LINUX = 1 # Linux OS
WINDOWS = 2 # Windows OS

# Imports
import os
current_os = WINDOWS if (os.name == 'nt') else LINUX # Detect whether we're on Windows or Linux
import time
if (current_os == LINUX):
    import serial


# Constants
RANKS = "12345678"
FILES_STANDARD = "abcdefgh"
FILES_BANK1 = "wx"
FILES_BANK2 = "yz"
FILES_BANKS = FILES_BANK1 + FILES_BANK2
ALL_FILES = FILES_STANDARD + FILES_BANKS
ALL_SQUARES = [file + rank for file in ALL_FILES for rank in RANKS]

BOTTOM_RIGHT_CORNER_X = 100
BOTTOM_RIGHT_CORNER_Y = 100
SQUARE_SIZE = 150

SERIAL_BAUD = 115200
USB_INTERFACES = [
    '/dev/ttyUSB0',
    '/dev/ttyUSB1',
    '/dev/ttyUSB2',
    '/dev/ttyUSB3'
]

class PhysicalBoard:
    def __init__(self):
        self.commandQueue = []
        self.arduinoQueueCount = 0
        self.arduinoQueueAvailableCount = 0
        self.serialInBuffer = ""
        self.finalDestinationFileRank = (0, 0) # (file, rank) coordinates
        self.__prevCheckReedSwitches = {}
        self.reedSwitches = {}
        for fileRank in ALL_SQUARES:
            self.__prevCheckReedSwitches[fileRank] = False
            self.reedSwitches[fileRank] = False
        
        if (current_os == LINUX):
            self.arduino = self.beginSerial()
        else:
            self.arduino = None

    @staticmethod
    def getFileRankCoords(square):
        # Error checking
        if (not isinstance(square, str)):
            print("square '" + str(square) + "' is not a string")
        if (len(square) != 2):
            print("Invalid square '" + str(square) + "'")

        # File
        file = 0
        if (square[0] in FILES_STANDARD):
            file = FILES_STANDARD.index(square[0])
        elif (square[0] in FILES_BANK1):
            file = -5 + FILES_BANK1.index(square[0])
        elif (square[0] in FILES_BANK2):
            file = -3 + FILES_BANK2.index(square[0])
        else:
            print("Invalid file '" + square[0] + "'")
        
        # Rank
        # Ensure numeric
        if (not square[1].isdigit()):
            print("Invalid rank '" + square[1] + "'")
        rank = int(square[1])

        fileRank = (file, rank)
        # More error checking
        if (not PhysicalBoard.checkInBounds(fileRank, printErrors=True)):
            print("Invalid square '" + square + "'")

        return fileRank

    @staticmethod
    def checkInBounds(fileRank, printErrors=False):
        # Ensures file and rank are inside the bounds of our board.
        (file, rank) = fileRank
        
        # Make sure file and rank are ints
        if (not isinstance(file, int) or not isinstance(rank, int)):
            if printErrors:
                print("Invalid file or rank '" + str(file) + "', '" + str(rank) + "'")
            return False
        if not (-5 <= file <= -2 or 0 <= file <= 7):
            if printErrors:
                print("Invalid file '" + str(file) + "'")
            return False
        if not (1 <= rank <= 8):
            if printErrors:
                print("Invalid rank '" + rank + "'")
            return False
        return True

    @staticmethod
    def getSquareFromFileRank(fileRank):
        (file, rank) = fileRank
        if (not PhysicalBoard.checkInBounds((file, rank), printErrors=True)):
            print("Invalid file/rank '" + str(file) + "', '" + str(rank) + "'")
            return None
        
        square = ''
        
        if (file >= 0):
            square += FILES_STANDARD[file]
        elif (-5 <= file <= -4):
            square += FILES_BANK1[file + 5]
        elif (-3 <= file <= -2):
            square += FILES_BANK2[file + 3]
        
        square += str(rank)
        
        return square

    @staticmethod
    def taxicabDistance(start, end):
        (startFile, startRank) = PhysicalBoard.getFileRankCoords(start)
        (endFile, endRank) = PhysicalBoard.getFileRankCoords(end)

        return abs(startFile - endFile) + abs(startRank - endRank)

    @staticmethod
    def getXY(square): # Takes input like 'f2' or 'w6' and returns xy coordinates
        (file, rank) = PhysicalBoard.getFileRankCoords(square)
        return PhysicalBoard.getXYFromFileRank((file, rank))

    @staticmethod
    def getXYFromFileRank(fileRankCoords):
        (file, rank) = fileRankCoords
        x = BOTTOM_RIGHT_CORNER_X + (rank - 1 + 0.5) * SQUARE_SIZE
        y = BOTTOM_RIGHT_CORNER_Y + (-file + 7 + 0.5) * SQUARE_SIZE
        return (int(x), int(y))

    @staticmethod
    def getPath(start, end, direct=False, includeStart=True):
        """
        Gets a path from start to end that is garunteed not to cross any other squares (unless direct is True).

        start and end are in the form of 'f2' or 'w6'.
        direct: If True, the path will only include the start and end squares.
        includeStart: If True, the start square will be included in the path.

        Example path:
        + - + - + - + - + - +
        :   :   :   :[E]:   :
        + - + - + - 3 - + - +
        :   :   :   ^   :   :
        + - 1------>2 - + - +
        :[S]:   :   :   :   :
        + - + - + - + - + - +
        """
        path = [] # List of (file, rank) tuples
        (startFile, startRank) = PhysicalBoard.getFileRankCoords(start)
        (endFile, endRank) = PhysicalBoard.getFileRankCoords(end)

        if (includeStart):
            path.append((startFile, startRank))
        
        # Ensure start != end
        if (startFile == endFile and startRank == endRank):
            return path

        if (direct):
            path.append((endFile, endRank))
        else:
            # Initial values for waypoints
            waypoint1 = [startFile, startRank]
            # Note: waypoint2 is calculated only when needed
            waypoint3 = [endFile, endRank]
            
            fileDistance = abs(startFile - endFile)
            rankDistance = abs(startRank - endRank)
            includeWaypoint2 = fileDistance > 1 and rankDistance > 1

            # File change
            if (startFile < endFile): # Need to move right (+file)
                waypoint1[0] += 0.5
                waypoint3[0] -= 0.5
            elif (startFile > endFile): # Need to move left (-file)
                waypoint1[0] -= 0.5
                waypoint3[0] += 0.5
            else: # startFile == endFile (move waypoints towards center - rank = 3.5)
                if (startFile < 3.5):
                    waypoint1[0] += 0.5
                    waypoint3[0] += 0.5
                else:
                    waypoint1[0] -= 0.5
                    waypoint3[0] -= 0.5
            
            # Rank change
            if (startRank < endRank):
                waypoint1[1] += 0.5
                waypoint3[1] -= 0.5
            elif (startRank > endRank):
                waypoint1[1] -= 0.5
                waypoint3[1] += 0.5
            else: # startRank == endRank (move waypoints towards center - file = 4.5)
                if (startRank < 4.5):
                    waypoint1[1] += 0.5
                    waypoint3[1] += 0.5
                else:
                    waypoint1[1] -= 0.5
                    waypoint3[1] -= 0.5

            # Add waypoints
            path.append((waypoint1[0], waypoint1[1]))
            if (includeWaypoint2):
                waypoint2 = [waypoint3[0], waypoint1[1]] # New file, same rank
                path.append((waypoint2[0], waypoint2[1]))
            path.append((waypoint3[0], waypoint3[1]))

            # Add end
            path.append((endFile, endRank))
        return path
    

    @staticmethod
    def buildCommand(x, y, magnetUp, optimizeRoute):
        x = int(x)
        y = int(y)
        if x < 0 or x > 9999 or y < 0 or y > 9999:
            print("Command to move to X: " + str(x) + ", Y: " + str(y) + " out of command size (positive, max 4 digits).")
            exit()

        magnetChar = 'U' if magnetUp else 'D' # Up vs Down
        optimizeChar = 'O' if optimizeRoute else 'P' # Optimize vs Precise
        splitCommand = [magnetChar, optimizeChar, 'X', str(x).zfill(4), 'Y', str(y).zfill(4)]
        command = "".join(splitCommand)

        return command

    @staticmethod
    def getCommands(start, end, direct=False, includeStart=True, useMagnetWithDirect=True):
        path = PhysicalBoard.getPath(start, end, direct, includeStart)
        commands = []

        for pathIndex in range(len(path)):
            isFirstCommand = (pathIndex == 0)
            isLastCommand = (pathIndex + 1 == len(path))
            (x, y) = PhysicalBoard.getXYFromFileRank(path[pathIndex])

            if (direct):
                commands.append(PhysicalBoard.buildCommand(x, y, magnetUp=((not isFirstCommand or not includeStart) and useMagnetWithDirect), optimizeRoute=False))
            elif (isFirstCommand and includeStart):
                # Move directly to start with magnet down, if applicable
                commands.append(PhysicalBoard.buildCommand(x, y, magnetUp=False, optimizeRoute=False))
            elif (isLastCommand):
                # Move precisely to end, without optimizing
                commands.append(PhysicalBoard.buildCommand(x, y, magnetUp=True, optimizeRoute=False))
            else:
                commands.append(PhysicalBoard.buildCommand(x, y, magnetUp=True, optimizeRoute=True))
        
        return commands
    
    def enqueueCommand(self, command):
        self.commandQueue.append(command)
    
    def enqueueCommands(self, commands):
        for command in commands:
            self.enqueueCommand(command)

    def dequeueCommand(self):
        if (len(self.commandQueue) > 0):
            return self.commandQueue.pop(0)
    
    def beginSerial(self):
        # Open serial connection to Arduino
        connected = False
        trying_interface = 0
        while (not connected):
            try:
                print("Looking for Arduino on USB" + str(trying_interface) + "...")
                arduino = serial.Serial(USB_INTERFACES[trying_interface], SERIAL_BAUD, timeout=1)
                arduino.flush()
                connected = True
            except serial.SerialException as e:
                print("Error connecting to Arduino (" + str(e) + "). Retrying...")
                time.sleep(0.2)

                trying_interface += 1
                if trying_interface >= len(USB_INTERFACES):
                    trying_interface = 0


        print("Connected to Arduino on " + USB_INTERFACES[trying_interface])
        arduino.flush()
        return arduino

    def receiveTelemetry(self):
        # Process incoming telemetry messages from Arduino, and processes the most recent message.
        # Updates self.arduinoQueueAvailableCount and other things from Arduino serial telemetry
        if (self.arduino.in_waiting > 0):
            # Each telemetry message ends in a newline.
            self.serialInBuffer += self.arduino.read(self.arduino.in_waiting).decode()
        
        message = ""

        # Loop through until we hit a newline or end of buffer
        continueReading = True
        charCounter = 0
        while (continueReading):
            if (charCounter >= len(self.serialInBuffer)):
                # End of buffer
                continueReading = False

            elif (self.serialInBuffer[charCounter] == '\n'):
                # Process message
                message = self.serialInBuffer[:charCounter].lstrip('\r\n').rstrip('\r\n')
                self.serialInBuffer = self.serialInBuffer[charCounter+1:]
                charCounter = 0
            
            charCounter += 1
        
        if (message != ""):
            if len(message) >= 5 and "ERROR" in message:
                print("Arduino error: " + message)
            else:
                # Message format is:
                # <queueCount>,<queueAvailableCount>\n
                # Example: "3,5"
                splitMessage = message.split(',')

                """
                if(len(splitMessage) != 2):
                    print("Invalid telemetry message: " + message)
                    return
                """
                
                self.arduinoQueueCount = int(splitMessage[0])
                self.arduinoQueueAvailableCount = int(splitMessage[1])
            
            print("Received telemetry: " + message) # Debugging

    
    def sendNextCommandIfAvailable(self):
        # Sends next command to the Arduino if it's ready
        self.receiveTelemetry()

        if (len(self.commandQueue) > 0 and self.arduinoQueueAvailableCount > 0):
            command = self.dequeueCommand()
            command = '#' + command # start character
            print("Sending command: " + command)
            self.arduino.write(command.encode())

            self.arduinoQueueCount += 1
            self.arduinoQueueAvailableCount -= 1

    def update(self):
        # Updates telemetry and sends next command if available
        self.receiveTelemetry()
        self.sendNextCommandIfAvailable()

    def totalQueueCount(self):
        # How many commands must be executed until we are done (does not include current command in progress)
        return len(self.commandQueue) + self.arduinoQueueCount == 0

    def __movePiece(self, start, end, direct=False, useMagnetWithDirect=True):
        notAtStart = PhysicalBoard.getFileRankCoords(start) != self.finalDestinationFileRank

        commands = PhysicalBoard.getCommands(start, end, direct=direct, includeStart=notAtStart, useMagnetWithDirect=useMagnetWithDirect)
        self.finalDestinationFileRank = PhysicalBoard.getFileRankCoords(end)
        self.enqueueCommands(commands)

    def movePiece(self, start, end, direct=False):
        self.__movePiece(start, end, direct=direct, useMagnetWithDirect=True)
    
    def moveWithoutMagnet(self, start, end):
        self.__movePiece(start, end, direct=True, useMagnetWithDirect=False)
    
    def updateReedSwitches(self):
        # TODO: Implement this with the muxes
        pass

    def getModifiedReedSwitches(self):
        # Compare current state to state from last check to see what the user changed.
        self.updateReedSwitches()
        modifiedReedSwitches = {}
        for square in ALL_SQUARES:
            if (self.__prevCheckReedSwitches[square] != self.reedSwitches[square]):
                modifiedReedSwitches[square] = self.reedSwitches[square]

        return modifiedReedSwitches
    
    def debugRunRectanglesAroundBoard(self):
        # Debugging function to run rectangles around the board, until the user stops it.
        # Start at lower right corner of board, then lower left, then upper left, then upper right.

        optimize = True

        lowerRightCommand = PhysicalBoard.buildCommand(BOTTOM_RIGHT_CORNER_X, BOTTOM_RIGHT_CORNER_Y, optimizeRoute=optimize, magnetUp=False)
        lowerLeftCommand = PhysicalBoard.buildCommand(BOTTOM_RIGHT_CORNER_X, BOTTOM_RIGHT_CORNER_Y + 13*SQUARE_SIZE, optimizeRoute=optimize, magnetUp=False)
        upperLeftCommand = PhysicalBoard.buildCommand(BOTTOM_RIGHT_CORNER_X + 8*SQUARE_SIZE, BOTTOM_RIGHT_CORNER_Y + 13*SQUARE_SIZE, optimizeRoute=optimize, magnetUp=False)
        upperRightCommand = PhysicalBoard.buildCommand(BOTTOM_RIGHT_CORNER_X + 8*SQUARE_SIZE, BOTTOM_RIGHT_CORNER_Y, optimizeRoute=optimize, magnetUp=False)

        while True:
            if (len(self.commandQueue) == 0):
                self.enqueueCommand(lowerRightCommand)
                self.enqueueCommand(lowerLeftCommand)
                self.enqueueCommand(upperLeftCommand)
                self.enqueueCommand(upperRightCommand)
            self.update()
            time.sleep(0.25)