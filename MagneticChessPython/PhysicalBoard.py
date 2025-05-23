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
import serial
import serial.tools.list_ports

# Constants
RANKS = "12345678"
FILES_STANDARD = "abcdefgh"
FILES_BANK1 = "wx"
FILES_BANK2 = "yz"
FILES_BANKS = FILES_BANK1 + FILES_BANK2
ALL_FILES = FILES_BANKS + FILES_STANDARD
ALL_SQUARES = [file + rank for file in ALL_FILES for rank in RANKS]

# Calibration values for advanced pathing
# BANK ----------------------------------------
# TOP LEFT CORNER: 157, 45
BANK_TOP_LEFT_CORNER_X = 1870
BANK_TOP_LEFT_CORNER_Y = 3037

# TOP RIGHT CORNER: 159, 870
BANK_TOP_RIGHT_CORNER_X = 1870
BANK_TOP_RIGHT_CORNER_Y = 2127

# BOTTOM LEFT CORNER: 1800, 45
BANK_BOTTOM_LEFT_CORNER_X = 30
BANK_BOTTOM_LEFT_CORNER_Y = 3037

# BOTTOM RIGHT CORNER: 1790, 855
BANK_BOTTOM_RIGHT_CORNER_X = 30
BANK_BOTTOM_RIGHT_CORNER_Y = 2127

# BOARD ---------------------------------------
# TOP LEFT CORNER: 145, 1005
BOARD_TOP_LEFT_CORNER_X = 30
BOARD_TOP_LEFT_CORNER_Y = 1900

# TOP RIGHT CORNER: 145, 2671
BOARD_TOP_RIGHT_CORNER_X = 1870
BOARD_TOP_RIGHT_CORNER_Y = 80

# BOTTOM LEFT CORNER: 1805, 1005
BOARD_BOTTOM_LEFT_CORNER_X = 30
BOARD_BOTTOM_LEFT_CORNER_Y = 1900

# BOTTOM RIGHT CORNER: 1805, 2671
BOARD_BOTTOM_RIGHT_CORNER_X = 30
BOARD_BOTTOM_RIGHT_CORNER_Y = 80

SQUARE_SIZE = 227.5

SERIAL_BAUD = 115200
LINUX_USB_INTERFACES = [
    '/dev/ttyUSB0',
    '/dev/ttyUSB1',
    '/dev/ttyUSB2',
    '/dev/ttyUSB3'
]

HOME_COMMAND = 'HPX0000Y0000' # Command to home the motors

class PhysicalBoard:
    def __init__(self):
        self.commandQueue = []
        self.isArduinoBusy = False
        self.firstAvailableTime = time.time()
        self.arduinoQueueCount = 0
        self.arduinoQueueAvailableCount = 0
        self.serialInBuffer = ""
        self.finalDestinationFileRank = (0, 1) # (file, rank) coordinates
        self.__prevCheckReedSwitches = {}
        self.reedSwitches = {}
        self.arcadeButtons = [False, False, False, False, False, False] # 6 arcade switches
        for fileRank in ALL_SQUARES:
            self.__prevCheckReedSwitches[fileRank] = False
            self.reedSwitches[fileRank] = False

        self.arduino = self.beginSerial()
        self.home() # Home motors after connecting

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
        return PhysicalBoard.getDistortedXYFromFileRank((file, rank))

    @staticmethod
    def getXYFromFileRank(fileRankCoords):
        (file, rank) = fileRankCoords
        if (file < 0):
            topLeftX = BANK_TOP_LEFT_CORNER_X
            topLeftY = BANK_TOP_LEFT_CORNER_Y
            relativeFile = file + 5
        else:
            topLeftX = BOARD_TOP_LEFT_CORNER_X
            topLeftY = BOARD_TOP_LEFT_CORNER_Y
            relativeFile = file
        
        x = topLeftX + (8 - rank + 0.5) * SQUARE_SIZE
        y = topLeftY + (relativeFile + 0.5) * SQUARE_SIZE
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
    def getWeightedMidpoint(startXY, endXY, ratio=0.5):
        # Returns the weighted midpoint between two points, where ratio is how much closer to the second point it is, between 0 and 1.
        (startX, startY) = startXY
        (endX, endY) = endXY
        midX = (1-ratio) * startX + ratio * endX
        midY = (1-ratio) * startY + ratio * endY
        return (midX, midY)
    
    @staticmethod
    def getDistortedXY(squaresFromLowerLeftCorner, topLeftXY, topRightXY, bottomLeftXY, bottomRightXY, numFiles=8, numRanks=8):
        # Returns the distorted coordinates of a square on the board, given the relative number of squares from the lower left corner in both dimensions.
        (squaresX, squaresY) = squaresFromLowerLeftCorner

        ratioX = (squaresX / numFiles)
        ratioY = 1 - (squaresY / numRanks)

        topMidpoint = PhysicalBoard.getWeightedMidpoint(topLeftXY, topRightXY, ratioX)
        bottomMidpoint = PhysicalBoard.getWeightedMidpoint(bottomLeftXY, bottomRightXY, ratioX)
        distortedXY = PhysicalBoard.getWeightedMidpoint(topMidpoint, bottomMidpoint, ratioY)
        return distortedXY

    @staticmethod
    def getDistortedXYFromFileRank(fileRank):
        # Returns the distorted coordinates of a square on the board, given the file/rank coordinates.
        (file, rank) = fileRank
        if (file < 0):
            topLeftXY = (BANK_TOP_LEFT_CORNER_X, BANK_TOP_LEFT_CORNER_Y)
            topRightXY = (BANK_TOP_RIGHT_CORNER_X, BANK_TOP_RIGHT_CORNER_Y)
            bottomLeftXY = (BANK_BOTTOM_LEFT_CORNER_X, BANK_BOTTOM_LEFT_CORNER_Y)
            bottomRightXY = (BANK_BOTTOM_RIGHT_CORNER_X, BANK_BOTTOM_RIGHT_CORNER_Y)
            numFiles = 4
            relativeSquareCount = (file + 5.5, rank - 0.5)
        else:
            topLeftXY = (BOARD_TOP_LEFT_CORNER_X, BOARD_TOP_LEFT_CORNER_Y)
            topRightXY = (BOARD_TOP_RIGHT_CORNER_X, BOARD_TOP_RIGHT_CORNER_Y)
            bottomLeftXY = (BOARD_BOTTOM_LEFT_CORNER_X, BOARD_BOTTOM_LEFT_CORNER_Y)
            bottomRightXY = (BOARD_BOTTOM_RIGHT_CORNER_X, BOARD_BOTTOM_RIGHT_CORNER_Y)
            numFiles = 8
            relativeSquareCount = (file + 0.5, rank - 0.5)
        
        return PhysicalBoard.getDistortedXY(relativeSquareCount, topLeftXY, topRightXY, bottomLeftXY, bottomRightXY, numFiles=numFiles, numRanks=8)

    @staticmethod
    def getPathAdvanced(start, end, direct=False, includeStart=True):
        """
        Gets a path from start to end that is garunteed not to cross any other squares (unless direct is True).

        start and end are in the form of 'f2' or 'w6'.
        direct: If True, the path will only include the start and end squares.
        includeStart: If True, the start square will be included in the path.

        Example path:
        + - + - + - + - + - +
        :   :   :   :[E]:   :
        + - + - + - 4 - + - +
        :   :   :   ^   :   :
        + - 1-->2-->3 - + - +
        :[S]:   :   :   :   :
        + - + - + - + - + - +
        """
        path = []
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
            # Waypoints are defined for every square corner (intersection) we hit.
            waypoints = []
            
        
    
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
            (x, y) = PhysicalBoard.getDistortedXYFromFileRank(path[pathIndex])

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
    
    @staticmethod
    def testBit(num, offset):
        num = int(num)
        mask = 1 << offset
        return (num & mask) > 0
    
    def isAllCommandsFinished(self):
        return len(self.commandQueue) == 0 and self.arduinoQueueCount == 0 and not self.isArduinoBusy

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
        if (current_os == LINUX):
            while (not connected):
                try:
                    print("Looking for Arduino on USB" + str(trying_interface) + "...")
                    arduino = serial.Serial(LINUX_USB_INTERFACES[trying_interface], SERIAL_BAUD, timeout=1)
                    arduino.flush()
                    connected = True
                except serial.SerialException as e:
                    print("Error connecting to Arduino. Retrying...")
                    time.sleep(0.2)

                    trying_interface += 1
                    if trying_interface >= len(LINUX_USB_INTERFACES):
                        trying_interface = 0

            print("Connected to Arduino on " + LINUX_USB_INTERFACES[trying_interface])
            arduino.flush()
        else: # OS is Windows
            while (not connected):
                try:
                    ports = serial.tools.list_ports.comports()
                    device = None
                    for port in ports:
                        if 'CH340' in port.description: # Arduino chip
                            device = port
                            break
                    if device:
                        print("Looking for Arduino on " + device.name)
                        arduino = serial.Serial(device.name, SERIAL_BAUD, timeout=1)
                        arduino.flush()
                        connected = True
                    else:
                        raise serial.SerialException()
                except serial.SerialException as e:
                    print("Error connecting to Arduino. Retrying...")
                    time.sleep(0.2)

            print("Connected to Arduino on " + device.name)
            arduino.flush()

        return arduino

    def receiveTelemetry(self):
        # Process incoming telemetry messages from Arduino, and processes the most recent message.
        # Updates self.arduinoQueueAvailableCount and other things from Arduino serial telemetry
        if (self.arduino.in_waiting > 0):
            # Each telemetry message ends in a newline.
            incoming_serial = self.arduino.read(self.arduino.in_waiting)
            try:
                additional = incoming_serial.decode()
                self.serialInBuffer += additional
            except UnicodeDecodeError:
                print("WARNING: Recieved corrupted telemetry data. Ignored and cleared buffer. This will likely cause more errors.")
                self.serialInBuffer = ""
        
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
                # <Finished/Executing (F/E),<queueCount>,<queueAvailableCount>,<Arcade Switch count since last message (hex)>\n
                # Example: "F,3,5,3f\n",

                splitMessage = message.rstrip('\n\r').split(',')

                if(len(splitMessage) != 3):
                    print("Invalid telemetry message: " + message)
                    return
                
                busy = splitMessage[0] == 'E'
                if (not busy and self.isArduinoBusy and len(self.commandQueue) == 0 and self.arduinoQueueCount == 0):
                    self.firstAvailableTime = time.time()
                self.isArduinoBusy = busy
                self.arduinoQueueCount = int(splitMessage[1])
                self.arduinoQueueAvailableCount = int(splitMessage[2])
                #self.setReedSwitchesFromHex(splitMessage[3])
                #self.setArcadeSwitchesFromHex(splitMessage[3])
            
            # print("Received telemetry: " + message) # Debugging

    def setReedSwitchesFromHex(self, hexString):
        # Reed switches are stored in a hex string, with each bit representing a switch.
        # It's in big-endian format, so the last switch is the most significant bit of the first byte.

        # Grab first two characters of hex string, then second, then third, etc.
        # At the same time, count columns backwards from 11 to 0, inclusive.
        columnIndex = 11 # Index of the column we're on, in ALL_FILES
        for i in range(0, len(hexString), 2):
            hexByte = hexString[i:i+2] # Grab two characters
            byte = int(hexByte, 16) # Convert to integer
            for rowIndex in range(7): # Loop form 0 to 7, inclusive
                squareName = ALL_FILES[columnIndex] + str(rowIndex + 1)
                isOn = PhysicalBoard.testBit(byte, rowIndex) # Get whether the switch is on
                self.reedSwitches[squareName] = isOn
            columnIndex -= 1
    
    def setArcadeSwitchesFromHex(self, hexString):
        # Sets the 6 arcade switch values from 2 hex characters
        if (len(hexString) != 2):
            print("Invalid arcade switch hex string: " + hexString)
            return
        
        byte = int(hexString, 16)
        for i in range(6):
            self.arcadeButtons[i] = PhysicalBoard.testBit(byte, i)
    
    def sendNextCommandIfAvailable(self):
        # Sends next command to the Arduino if it's ready
        self.receiveTelemetry()

        if (len(self.commandQueue) > 0 and self.arduinoQueueAvailableCount > 3):
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

    def home(self):
        # Homes the motors by sending a command beginning with 'H'
        self.commandQueue = [] # Clear any existing commands
        self.enqueueCommand(HOME_COMMAND) # Send home command
        self.sendNextCommandIfAvailable()

    def motorTestRun(self):
        self.moveWithoutMagnet('h1', 'h1') # Starting square

        # Rectangle around the board
        self.movePiece('h1', 'w1', True)
        time.sleep(1)
        self.movePiece('w1', 'w8', True)
        time.sleep(1)
        self.movePiece('w8', 'h8', True)
        time.sleep(1)
        self.movePiece('h8', 'h1', True)
        time.sleep(1)

        # Back and forth, horizontal
        self.movePiece('h1', 'w2')
        self.movePiece('w2', 'h2', True)
        self.movePiece('h2', 'w3')
        self.movePiece('w3', 'h3', True)
        self.movePiece('h3', 'w4')
        self.movePiece('w4', 'h4', True)
        self.movePiece('h4', 'w5')
        self.movePiece('w5', 'h5', True)
        self.movePiece('h5', 'w6')
        self.movePiece('w6', 'h6', True)
        self.movePiece('h6', 'w7')
        self.movePiece('w7', 'h7', True)
        self.movePiece('h7', 'w8')
        time.sleep(1)

        # Back and forth, vertical
        self.movePiece('w8', 'x1')
        self.movePiece('x1', 'x8', True)
        self.movePiece('x8', 'y1')
        self.movePiece('y1', 'y8', True)
        self.movePiece('y8', 'z1')
        self.movePiece('z1', 'z8', True)
        self.movePiece('z8', 'a1')
        self.movePiece('a1', 'a8', True)
        self.movePiece('a8', 'b1')
        self.movePiece('b1', 'b8', True)
        self.movePiece('b8', 'c1')
        self.movePiece('c1', 'c8', True)
        self.movePiece('c8', 'd1')
        self.movePiece('d1', 'd8', True)
        self.movePiece('d8', 'e1')
        self.movePiece('e1', 'e8', True)
        self.movePiece('e8', 'f1')
        self.movePiece('f1', 'f8', True)
        self.movePiece('f8', 'g1')
        self.movePiece('g1', 'g8', True)
        self.movePiece('g8', 'h1')


    def getModifiedReedSwitches(self):
        # Compare current state to state from last check to see what the user changed.
        modifiedReedSwitches = {}
        for square in ALL_SQUARES:
            if (self.__prevCheckReedSwitches[square] != self.reedSwitches[square]):
                modifiedReedSwitches[square] = self.reedSwitches[square]

        return modifiedReedSwitches
