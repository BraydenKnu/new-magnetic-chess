
import time
import RPi.GPIO as GPIO
import math
from time import sleep
from datetime import datetime, timedelta

#
# CORE-XY SYSTEM WITH MOTORS A AND B
# ___________
# |         |
# |         |
# |----O----|
# |         |
# |         |
# A_________B
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

# Rotations
DISABLED = -1
COUNTER_CLOCKWISE = 0
CLOCKWISE = 1

# Motor Settings
# (en_motor1, en_motor2, dir_motor_a, dir_motor_b)
MOTOR_SETTINGS = {
    UP:         (COUNTER_CLOCKWISE, CLOCKWISE        ),
    DOWN:       (CLOCKWISE,         COUNTER_CLOCKWISE),
    LEFT:       (CLOCKWISE,         CLOCKWISE        ),
    RIGHT:      (COUNTER_CLOCKWISE, COUNTER_CLOCKWISE),
    UP_LEFT:    (DISABLED,          CLOCKWISE        ),
    UP_RIGHT:   (COUNTER_CLOCKWISE, DISABLED         ),
    DOWN_LEFT:  (CLOCKWISE,         DISABLED         ),
    DOWN_RIGHT: (DISABLED,          COUNTER_CLOCKWISE)
}

PIN_STEP_MOTOR_A = 18
PIN_DIR_MOTOR_A = 19
PIN_STEP_MOTOR_B = 20
PIN_DIR_MOTOR_B = 21
PIN_EN = 22

STEPS_PER_REV = 400
SPEED = 1000

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_STEP_MOTOR_A, GPIO.OUT)
GPIO.setup(PIN_DIR_MOTOR_A, GPIO.OUT)
GPIO.setup(PIN_STEP_MOTOR_B, GPIO.OUT)
GPIO.setup(PIN_DIR_MOTOR_B, GPIO.OUT)
GPIO.setup(PIN_EN, GPIO.OUT)

GPIO.output(PIN_EN, 0)

# current values
motor_a_dir = 0
motor_b_dir = 0

GPIO.output(PIN_DIR_MOTOR_A, motor_a_dir)
GPIO.output(PIN_DIR_MOTOR_B, motor_b_dir)

def step_advanced(motor_a, motor_b, dir1, dir2):
    global motor_a_dir
    global motor_b_dir
    # set directions if they have changed
    if dir1 != motor_a_dir:
        GPIO.output(PIN_DIR_MOTOR_A, dir1)
        motor_a_dir = dir1
    if dir2 != motor_b_dir:
        GPIO.output(PIN_DIR_MOTOR_B, dir2)
        motor_b_dir = dir2

    # Try and fire motors at the same time (GPIO.output is a bit slow)
    if motor_a:
        GPIO.output(PIN_STEP_MOTOR_A, 1)
    if motor_b:
        GPIO.output(PIN_STEP_MOTOR_B, 1)
    
    sleep(0.0001) # Wait for motors to fire

    if motor_a:
        GPIO.output(PIN_STEP_MOTOR_A, 0)
    if motor_b:
        GPIO.output(PIN_STEP_MOTOR_B, 0)

def step(direction):
    dir_motor_a, dir_motor_b = MOTOR_SETTINGS[direction]
    motor_a = dir_motor_a != DISABLED
    motor_b = dir_motor_b != DISABLED
    step_advanced(motor_a, motor_b, dir_motor_a, dir_motor_b)

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
    move(DOWN_RIGHT, 1000)
    move(DOWN_LEFT, 1000)

finally:
    # Spin down motors
    sleep(0.2)

    # Cleanup GPIO
    GPIO.output(PIN_EN, 1)
    GPIO.cleanup()
