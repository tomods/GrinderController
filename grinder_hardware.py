from machine import Pin, ADC
# from enum import Enum # Not supported by MicroPython!

from grinder_filter import GrinderFilter
from grinder_debouncer import GrinderDebouncer
from RP2040ADC import Rp2040AdcDmaAveraging

BUTTON_PIN = 3
JACK_FET_PIN = 1
MOTOR_FET_PIN = 5
VOLTAGE_PIN = 29  # measuring VSYS/3 on Pico

VOLTAGE_THRESH_LOW = 1000
VOLTAGE_THRESH_HIGH = 3000

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

    def __init__(self):
        self._button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
        self._jack_fet = Pin(JACK_FET_PIN, Pin.OUT, value=0)
        self._motor_fet = Pin(MOTOR_FET_PIN, Pin.OUT, value=1)
        # self._voltage_adc = ADC(Pin(VOLTAGE_PIN))
        self._avg_adc = Rp2040AdcDmaAveraging(gpio_pin=VOLTAGE_PIN, dma_chan=0, adc_samples=16)

        self._debounce = GrinderDebouncer(initial_value=1, debounce_time_ms=DEBOUNCE_TIME_MS)
        # self._filter = GrinderFilter(initial_value=VOLTAGE_THRESH_HIGH, filter_size=VOLTAGE_FILTER_SIZE)

        # Start first ADC DMA capture, so that the first run() will have something to read
        self._avg_adc.capture_start()

    @staticmethod
    def _adc_to_voltage(adc_val):
        # FIXME Maybe actually convert?!
        return adc_val

    def read_voltage(self):
        # return self._adc_to_voltage(self._filter.filter_value(self._voltage_adc.read_u16()))
        # return self._avg_adc.read_u16()
        value = self._avg_adc.wait_and_read_average_u12()

        # Restart ADC DMA capture for next run()
        self._avg_adc.capture_start()
        return value

    def read_button_state(self):
        debounced = self._debounce.debounce_button(self._button.value())
        return GrinderHardware.ButtonState.PRESSED if debounced == 0 else GrinderHardware.ButtonState.RELEASED

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
