
import time
import RPi.GPIO as GPIO
import math
from time import sleep
from datetime import datetime, timedelta

STEP_M1 = 18
DIR_M1 = 19
STEP_M2 = 20
DIR_M2 = 21
EN = 22

STEPS_PER_REV = 1600

SPEED = 1600

GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_M1, GPIO.OUT)
GPIO.setup(DIR_M1, GPIO.OUT)
GPIO.setup(STEP_M2, GPIO.OUT)
GPIO.setup(DIR_M2, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.output(EN, 0)

Xdir = 0
Ydir = 0

GPIO.output(DIR_M1, Xdir)
GPIO.output(DIR_M2, Ydir)

def step(motor):
    if motor == 0:
        GPIO.output(STEP_M1, 1)
        GPIO.output(STEP_M1, 0)
    if motor == 1:
        GPIO.output(STEP_M2, 1)
        GPIO.output(STEP_M2, 0)

def multi_steps(motor, direction, steps):
    if motor == 0:
        GPIO.output(DIR_M1, direction)
    if motor == 1:
        GPIO.output(DIR_M2, direction)
    
    period = 1.0/SPEED
    for i in range(0, steps):
        next_time = datetime.now() + timedelta(seconds=period)

        current_time = datetime.now()

        # Wait until the next step is due
        while current_time < next_time:
            current_time = datetime.now()
        
        step(motor)

try:
    # do a diamond shape
    multi_steps(0, 1, 500)
    multi_steps(1, 1, 500)
    multi_steps(0, 0, 500)
    multi_steps(1, 0, 500)
    
    # Test EN pin on and off
    for i in range(3):
        GPIO.output(EN, 1)
        sleep(0.5)
        GPIO.output(EN, 0)
        sleep(0.5)

finally:
    # Cleanup GPIO
    GPIO.output(EN, 1)
    GPIO.cleanup()
