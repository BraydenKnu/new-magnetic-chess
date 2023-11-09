import RPi.GPIO as GPIO
import math
from time import sleep
from datetime import datetime, timedelta

DIR = 18
STEP = 19
EN = 20

STEPS_PER_REV = 1600

acceleration = 1 # steps/sec^2


GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.output(EN, 0)
GPIO.output(DIR, 1)

def stepOne():
    GPIO.output(STEP, 1)
    GPIO.output(STEP, 0)

velocity = 0 # steps/sec

try:
    start_time = datetime.now()

    step_period = (-velocity + math.sqrt(velocity**2 + 4*acceleration))/(2*acceleration) 

    for i in range(STEPS_PER_REV):
        next_time = start_time + timedelta(seconds = (i+1) * step_period)
        stepOne()

        while(datetime.now() < next_time): # wait for the rest of the step period
            pass
    
    delta = (datetime.now() - start_time).total_seconds()
finally:
    sleep(0.1) # Allow motor time to come to a stop before disabling it
    GPIO.output(EN, 1)
    GPIO.cleanup()
