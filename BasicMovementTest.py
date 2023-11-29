
import time
import RPi.GPIO as GPIO
import math
from time import sleep
from datetime import datetime, timedelta

#
# CORE-XY SYSTEM
# ___________
# |         |
# |         |
# |----O----|
# |         |
# |         |
# M1_______M2
#

# Directions
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3
UP_LEFT = 4
UP_RIGHT = 5
DOWN_LEFT = 6
DOWN_RIGHT = 7

# Motor Settings
# (en_motor1, en_motor2, dir_motor1, dir_motor2)
MOTOR_SETTINGS = {
    UP:         (1, 1, 1, 1),
    DOWN:       (1, 1, 0, 0),
    LEFT:       (1, 1, 0, 1),
    RIGHT:      (1, 1, 1, 0),
    UP_LEFT:    (0, 1, 0, 1),
    UP_RIGHT:   (1, 0, 1, 0),
    DOWN_LEFT:  (0, 1, 1, 0),
    DOWN_RIGHT: (1, 0, 0, 1)
}

PIN_STEP_M1 = 18
PIN_DIR_M1 = 19
PIN_STEP_M2 = 20
PIN_DIR_M2 = 21
PIN_EN = 22

STEPS_PER_REV = 1600
SPEED = 1600

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_STEP_M1, GPIO.OUT)
GPIO.setup(PIN_DIR_M1, GPIO.OUT)
GPIO.setup(PIN_STEP_M2, GPIO.OUT)
GPIO.setup(PIN_DIR_M2, GPIO.OUT)
GPIO.setup(PIN_EN, GPIO.OUT)

GPIO.output(PIN_EN, 0)

# current values
m1_dir = 0
m2_dir = 0

GPIO.output(PIN_DIR_M1, m1_dir)
GPIO.output(PIN_DIR_M2, m2_dir)

def step_advanced(motor1, motor2, dir1, dir2):
    global m1_dir
    global m2_dir
    # set directions if they have changed
    if dir1 != m1_dir:
        GPIO.output(PIN_DIR_M1, dir1)
        m1_dir = dir1
    if dir2 != m2_dir:
        GPIO.output(PIN_DIR_M2, dir2)
        m2_dir = dir2

    # Try and fire motors at the same time (GPIO.output is a bit slow)
    if motor1:
        GPIO.output(PIN_STEP_M1, 1)
    if motor2:
        GPIO.output(PIN_STEP_M2, 1)
    
    if motor1:
        GPIO.output(PIN_STEP_M1, 0)
    if motor2:
        GPIO.output(PIN_STEP_M2, 0)

def step(direction):
    motor1, motor2, dir_m1, dir_m2 = MOTOR_SETTINGS[direction]
    step_advanced(motor1, motor2, dir_m1, dir_m2)

def move(direction, steps):
    period = 1.0/SPEED
    for i in range(0, steps):
        next_time = datetime.now() + timedelta(seconds=period)

        current_time = datetime.now()

        # Wait until the next step is due
        while current_time < next_time:
            current_time = datetime.now()
        
        step(direction)

try:
    move(UP, 1000)
    move(RIGHT, 1000)
    move(DOWN, 1000)
    move(LEFT, 1000)

    move(UP_LEFT, 1000)
    move(UP_RIGHT, 1000)
    move(DOWN_LEFT, 1000)
    move(DOWN_RIGHT, 1000)

finally:
    # Spin down motors
    sleep(0.2)

    # Cleanup GPIO
    GPIO.output(PIN_EN, 1)
    GPIO.cleanup()
