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

acceleration = 500 # steps/sec^2

GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_M1, GPIO.OUT)
GPIO.setup(DIR_M1, GPIO.OUT)
GPIO.setup(STEP_M2, GPIO.OUT)
GPIO.setup(DIR_M2, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.output(EN, 0)
GPIO.output(DIR_M1, 1)
GPIO.output(DIR_M2, 0)

def stepOne():
    GPIO.output(STEP_M1, 1)
    GPIO.output(STEP_M1, 0)

velocity = 0 # steps/sec

try:
    start_time = datetime.now()

    for i in range(STEPS_PER_REV * 2):
        step_period = (-velocity + math.sqrt(velocity**2 + 4*acceleration))/(2*acceleration)

        next_time = start_time + timedelta(seconds = (i+1) * step_period)
        stepOne()

        while(datetime.now() < next_time): # wait for the rest of the step period
            pass
        
        velocity = 1 / step_period

    start_time = datetime.now()
    for i in range(STEPS_PER_REV * 3):
        next_time = start_time + timedelta(seconds = (i+1) * step_period)
        stepOne()

        while(datetime.now() < next_time): # wait for the rest of the step period
            pass
    
    delta = (datetime.now() - start_time).total_seconds()
finally:
    sleep(0.1) # Allow motor time to come to a stop before disabling it
    GPIO.output(EN, 1)
    GPIO.cleanup()
