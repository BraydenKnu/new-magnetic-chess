











import pygame
import time
import RPi.GPIO as GPIO
import math
from time import sleep
from datetime import datetime, timedelta

DIR = 18
STEP_M1 = 19
DIR_M1 = 20
STEP_M2 = 21
DIR_M2 = 22
EN = 22

STEPS_PER_REV = 1600

SPEED_MULTIPLIER = 10

GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_M1, GPIO.OUT)
GPIO.setup(DIR_M1, GPIO.OUT)
GPIO.setup(STEP_M2, GPIO.OUT)
GPIO.setup(DIR_M2, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.output(EN, 0)

Xdir = 0
Ydir = 0

def step(motor):
    if motor == 0:
        GPIO.output(STEP_M1, 1)
        GPIO.output(STEP_M1, 0)
    if motor == 1:
        GPIO.output(STEP_M2, 1)
        GPIO.output(STEP_M2, 0)

def setDirections(Xvel, Yvel):
    global Xdir
    global Ydir

    # When changing directions, set the pins. Otherwise, ignore.
    if Xvel > 0 and Xdir != 1:
        GPIO.output(DIR_M1, 1)
        Xdir = 1
    elif Xvel < 0 and Xdir != 0:
        GPIO.output(DIR_M1, 0)
        Xdir = 0
    
    if Yvel > 0 and Ydir != 1:
        GPIO.output(DIR_M2, 1)
        Ydir = 1
    elif Yvel < 0 and Ydir != 0:
        GPIO.output(DIR_M2, 0)
        Ydir = 0


pygame.init()
pygame.joystick.init()


# Connect to conrtoller
controller = pygame.joystick.Joystick(0)
controller.init()

calibrations = [0, 0]

# Get joystick position
def getJS():
    pygame.event.pump()
    return [controller.get_axis(0), controller.get_axis(1)]

def getCalibratedJS():
    js = getJS()
    return [js[0] - calibrations[0], js[1] - calibrations[1]]

def calibrate():
    js = getJS()
    calibrations[0] = js[0]
    calibrations[1] = js[1]


lastXstepTime = datetime.now()
lastYstepTime = datetime.now()

calibrate()

try:
        
    while True:
        joystickInputs = getCalibratedJS()
        Xvel = joystickInputs[0] * SPEED_MULTIPLIER
        Yvel = joystickInputs[1] * SPEED_MULTIPLIER

        if controller.get_button(0): # If A is pressed, calibrate
            calibrate()

        if controller.get_button(1): # If B is pressed, exit.
            break
        
        # Get periods
        if (Xvel == 0):
            XstepPeriod = 0
        else:
            XstepPeriod = 1/Xvel

        if (Yvel == 0):
            YstepPeriod = 0
        else:
            YstepPeriod = 1/Yvel
        
        XnextTime = lastXstepTime + timedelta(XstepPeriod)
        YnextTime = lastYstepTime + timedelta(YstepPeriod)

        current_time = datetime.now()
        
        if current_time > XnextTime and Xvel != 0:
            step(0)
            lastXstepTime = current_time
        if current_time > YnextTime and Yvel != 0:
            step(1)
            lastYstepTime = current_time
finally:
    # Cleanup GPIO
    GPIO.output(EN, 1)
    GPIO.cleanup()
