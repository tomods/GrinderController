from machine import Pin, ADC
# from enum import Enum # Not supported by MicroPython!
import time

from grinder_filter import GrinderFilter

BUTTON_PIN = 3
JACK_FET_PIN = 1
MOTOR_FET_PIN = 5
VOLTAGE_PIN = 26

VOLTAGE_THRESH_LOW = 20000
VOLTAGE_THRESH_HIGH = 50000

AUTOGRIND_STOP_VOLTAGE_FACTOR = 1.1
AUTOGRIND_TIMEOUT_MS = 1000
AUTOGRIND_SAFETY_STOP_MS = 1000 * 60

DEBOUNCE_TIME_MS = 20
VOLTAGE_FILTER_SIZE = 16


class GrinderHardware:
    # Should be an Enum
    class ButtonState:
        PRESSED = 0
        RELEASED = 1

    # Should be an Enum
    class JackState:
        ENABLED = 0
        DISABLED = 1

    # Should be an Enum
    class MotorState:
        RUNNING = 0
        STOPPED = 1

    class Debouncer:
        def __init__(self):
            self._prev_button_state = 1
            self._button_change_time = time.ticks_ms()
            self._debounced_button_state = 1

        def debounce_button(self, pin_state):
            if pin_state != self._prev_button_state:
                self._prev_button_state = pin_state
                self._button_change_time = time.ticks_ms()
            elif pin_state != self._debounced_button_state:
                time_passed = time.ticks_diff(time.ticks_ms(), self._button_change_time)
                if time_passed > DEBOUNCE_TIME_MS:
                    self._debounced_button_state = pin_state

            return GrinderHardware.ButtonState.PRESSED if self._debounced_button_state == 0 \
                else GrinderHardware.ButtonState.RELEASED

    def __init__(self):
        self._button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self._jack_fet = Pin(JACK_FET_PIN, Pin.OUT, value=0)
        self._motor_fet = Pin(MOTOR_FET_PIN, Pin.OUT, value=1)
        self._voltage_adc = ADC(Pin(VOLTAGE_PIN))

        self._debounce = GrinderHardware.Debouncer()
        self._filter = GrinderFilter(VOLTAGE_THRESH_HIGH, VOLTAGE_FILTER_SIZE)

    @staticmethod
    def _adc_to_voltage(adc_val):
        # FIXME Maybe actually convert?!
        return adc_val

    def read_voltage(self):
        return self._adc_to_voltage(self._filter.filter_value(self._voltage_adc.read_u16()))

    def read_button_state(self) -> ButtonState:
        return self._debounce.debounce_button(self._button.value())

    def set_motor_state(self, val: MotorState):
        self._motor_fet.value(0 if val == GrinderHardware.MotorState.RUNNING else 1)

    def set_jack_state(self, val: JackState):
        self._jack_fet.value(0 if val == GrinderHardware.JackState.ENABLED else 1)

    @staticmethod
    def should_stop_charging(current_voltage):
        return current_voltage >= VOLTAGE_THRESH_HIGH

    @staticmethod
    def should_start_charging(current_voltage):
        return current_voltage <= VOLTAGE_THRESH_LOW

    @staticmethod
    def should_stop_grinding(current_voltage, start_voltage):
        return current_voltage >= start_voltage * AUTOGRIND_STOP_VOLTAGE_FACTOR
