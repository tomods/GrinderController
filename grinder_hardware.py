from machine import Pin, ADC
from enum import Enum
from collections import deque
import time

BUTTON_PIN = 3
JACK_FET_PIN = 1
MOTOR_FET_PIN = 5
VOLTAGE_PIN = 26

VOLTAGE_THRESH_LOW = 1000
VOLTAGE_THRESH_HIGH = 3000

AUTOGRIND_STOP_VOLTAGE_FACTOR = 1.1
AUTOGRIND_TIMEOUT_MS = 1000
AUTOGRIND_SAFETY_STOP_MS = 1000 * 60

DEBOUNCE_TIME_MS = 20
VOLTAGE_FILTER_SIZE = 16


class GrinderHardware:
    class ButtonState(Enum):
        PRESSED = 0
        RELEASED = 1

    class JackState(Enum):
        ENABLED = 0
        DISABLED = 1

    class MotorState(Enum):
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

    class Filter:
        def __init__(self):
            self._voltage_filter_list = deque(maxlen=VOLTAGE_FILTER_SIZE)
            self._voltage_filtered = 0

        @staticmethod
        def _adc_to_voltage(adc_val):
            # FIXME Maybe actually convert?!
            return adc_val

        def filter_voltage(self, adc_val):
            # TODO FIXME Take care of the beginning!!
            oldest = self._voltage_filter_list.popleft()
            self._voltage_filter_list.append(adc_val)
            # FIXME Is it actually clever to not use float here?
            self._voltage_filtered += (adc_val - oldest) // VOLTAGE_FILTER_SIZE

            return self._adc_to_voltage(self._voltage_filtered)

    def __init__(self):
        self._button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self._jack_fet = Pin(JACK_FET_PIN, Pin.OUT, value=0)
        self._motor_fet = Pin(MOTOR_FET_PIN, Pin.OUT, value=1)
        self._voltage_adc = ADC(Pin(VOLTAGE_PIN))

        self._debounce = GrinderHardware.Debouncer()
        self._filter = GrinderHardware.Filter()

    def read_voltage(self):
        return self._filter.filter_voltage(self._voltage_adc.read_u16())

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
