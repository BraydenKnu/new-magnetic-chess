"""
PHYSICAL BOARD

Controls the motors and the piece magnet by sending commands to the Arduino.


COORDINATE SYSTEM
      Bank1    Main Board     Bank2
      _____ _________________ _____
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

EXTENDED MOVE NOTATION
The board is extended to 12x8 to allow for the movement of the pieces to the banks.
For example, d2z1 is a valid move.

EXTENDED COORDINATE SYSTEM
To support moving pieces to the corners of each square, rank/file coordinates have been converted
to numeirc values, stored as (file, rank) tuples. A1 is at (0, 1).
"""

# Imports
import RPi.GPIO as GPIO
import serial
import time

# Constants
RANKS = "12345678"
FILES_STANDARD = "abcdefgh"
FILES_BANK1 = "wx"
FILES_BANK2 = "yz"
FILES_BANKS = FILES_BANK1 + FILES_BANK2
ALL_FILES = FILES_STANDARD + FILES_BANKS
ALL_SQUARES = [file + rank for file in ALL_FILES for rank in RANKS]

CALIBRATION_A1_CENTER_X = 500
CALIBRATION_A1_CETNER_Y = 500
SQUARE_SIZE = 100

SERIAL_BAUD = 9600

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
        self.arduino = self.beginSerial()

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
            file = -3 + FILES_BANK1.index(square[0])
        elif (square[0] in FILES_BANK2):
            file = 9 + FILES_BANK2.index(square[0])
        
        # Rank
        rank = int(square[1])

        # More error checking
        if (file not in [-3, -2, 0, 1, 2, 3, 4, 5, 6, 7, 9, 10]):
            print("Invalid file '" + square[0] + "'")
        if (rank not in [1, 2, 3, 4, 5, 6, 7, 8]):
            print("Invalid rank '" + square[1] + "'")

        return (file, rank)

    @staticmethod
    def getXY(square): # Takes input like 'f2' or 'w6' and returns xy coordinates
        (file, rank) = PhysicalBoard.getFileRankCoords(square)
        return PhysicalBoard.getXYFromFileRank((file, rank))

    @staticmethod
    def getXYFromFileRank(fileRankCoords):
        (file, rank) = fileRankCoords
        x = CALIBRATION_A1_CENTER_X + file * SQUARE_SIZE
        y = CALIBRATION_A1_CETNER_Y + rank * SQUARE_SIZE
        return (x, y)

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
        if x < 0 or x > 999999 or y < 0 or y > 999999:
            print("Command to move to X: " + str(x) + ", Y: " + str(y) + " out of command size (positive, max 6 digits).")
            exit()

        magnetChar = 'U' if magnetUp else 'D' # Up vs Down
        optimizeChar = 'O' if optimizeRoute else 'P' # Optimize vs Precise
        splitCommand = [magnetChar, optimizeChar, 'X', str(x).zfill(6), 'Y', str(y).zfill(6)]
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
        while (not connected):
            try:
                arduino = serial.Serial('/dev/ttyUSB0', SERIAL_BAUD, timeout=1)
                arduino.flush()
                connected = True
            except:
                print("Error connecting to Arduino. Retrying...")
                time.sleep(1)

        arduino = serial.Serial('/dev/ttyUSB0', SERIAL_BAUD, timeout=1)
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
                # <Xpos>,<Ypos>,<queueCount>,<queueAvailableCount>,<currentCommand>\n
                # Example: "100,200,3,5,DPX1000Y0"
                splitMessage = message.split(',')

                if(len(splitMessage) != 5):
                    print("Invalid telemetry message: " + message)
                    return
                
                self.arduinoQueueCount = int(splitMessage[2])
                self.arduinoQueueAvailableCount = int(splitMessage[3])
            
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
    
    