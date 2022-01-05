import time

from machine import Pin
from grinder_controller import GrinderController
from grinder_hardware import GrinderHardware


def say_hi():
    led = Pin(25, Pin.OUT, value=0)
    print("Hi")
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)
    led.value(1)


def main():
    say_hi()
    hw = GrinderHardware()
    ctrl = GrinderController(hw)
    while True:
        ctrl.run()


if __name__ == '__main__':
    main()
