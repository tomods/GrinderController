from grinder_controller import GrinderController
from machine import Pin, ADC
import time

BUTTON_PIN = 3
JACK_FET_PIN = 1
MOTOR_FET_PIN = 5
VOLTAGE_PIN = 26

VOLTAGE_THRESH_LOW = 1000
VOLTAGE_THRESH_HIGH = 3000

AUTOGRIND_STOP_VOLTAGE_FACTOR = 1.1

DEBOUNCE_TIME_MS = 20


class GrinderHardware:
    def __init__(self):
        self._button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self._jack_fet = Pin(JACK_FET_PIN, Pin.OUT, value=0)
        self._motor_fet = Pin(MOTOR_FET_PIN, Pin.OUT, value=1)
        self._adc = ADC(Pin(VOLTAGE_PIN))

        self._prev_button_state = 1
        self._button_change_time = time.ticks_ms()
        self._debounced_button_state = 1

    def _debounce_button(self, pin_state):
        if pin_state != self._prev_button_state:
            self._prev_button_state = pin_state
            self._button_change_time = time.ticks_ms()
        else:
            time_passed = time.ticks_diff(time.ticks_ms(), self._button_change_time)
            if time_passed > DEBOUNCE_TIME_MS:
                self._debounced_button_state = pin_state

        return GrinderController.ButtonState.PRESSED if self._debounced_button_state == 0 \
            else GrinderController.ButtonState.RELEASED

    @staticmethod
    def _adc_to_voltage(adc_val):
        # TODO Actually convert!
        return adc_val

    def _filter_voltage(self, adc_val):
        # TODO Actually filter!
        return self._adc_to_voltage(adc_val)

    def read_voltage(self):
        return self._filter_voltage(self._adc.read_u16())

    def read_button_state(self):
        return self._debounce_button(self._button.value())

    def set_motor_state(self, val):
        self._motor_fet.value(0 if val == GrinderController.MotorState.RUNNING else 1)

    def set_jack_state(self, val):
        self._jack_fet.value(0 if val == GrinderController.JackState.ENABLED else 1)

    @staticmethod
    def should_stop_charging(current_voltage):
        return current_voltage >= VOLTAGE_THRESH_HIGH

    @staticmethod
    def should_start_charging(current_voltage):
        return current_voltage <= VOLTAGE_THRESH_LOW

    @staticmethod
    def should_stop_grinding(current_voltage, start_voltage):
        return current_voltage >= start_voltage * AUTOGRIND_STOP_VOLTAGE_FACTOR
