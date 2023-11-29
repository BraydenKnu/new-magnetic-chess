import RPi.GPIO as GPIO
from time import sleep

PIN_EN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_EN, GPIO.OUT)

# Turn EN on and off 100 times / sec

for i in range(1000):
    GPIO.output(PIN_EN, 1)
    sleep(0.005)
    GPIO.output(PIN_EN, 0)
    sleep(0.005)

GPIO.cleanup()