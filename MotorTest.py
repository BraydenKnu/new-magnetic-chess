import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime, timedelta

DIR = 18
STEP = 19
EN = 20



STEPS_PER_REV = 1600
desired_rpm = 120

step_period = 60/(STEPS_PER_REV*desired_rpm)

EXPECTED_TIME = 60/desired_rpm

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(EN, GPIO.OUT)

GPIO.output(EN, 0)
GPIO.output(DIR, 1)

def stepOne():
    GPIO.output(STEP, 1)
    GPIO.output(STEP, 0)

try:
    start_time = datetime.now()

    for i in range(STEPS_PER_REV):
        next_time = start_time + timedelta(seconds = (i+1) * step_period)
        stepOne()

        while(datetime.now() < next_time): # wait for the rest of the step period
            pass
    
    delta = (datetime.now() - start_time).total_seconds()
    print(EXPECTED_TIME)
    print(delta)
    print("Error: " + str(round((delta - EXPECTED_TIME)/EXPECTED_TIME * 100 * 100)/100) + "%")
finally:
    sleep(0.1) # Allow motor time to come to a stop before disabling it
    GPIO.output(EN, 1)
    GPIO.cleanup()
