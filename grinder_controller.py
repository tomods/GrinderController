from grinder_controller_states import *
from grinder_hardware import GrinderHardware
import time


class GrinderController:

    @staticmethod
    def log(s: str) -> None:
        print('{} – {}'.format(time.ticks_ms(), s))

    def __init__(self, hw: GrinderHardware):
        self._hw = hw
        self._voltage = 0
        self._button_state = GrinderHardware.ButtonState.RELEASED
        self._state = IdleState()  # init only
        self.state = self._state  # call setter
        self._run_count = 0
        self._last_run_time = time.ticks_ms()

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, state: State):
        self._state = state
        self._state.context = self
        self._state.on_enter()

    def run(self):
        self._run_count += 1
        # Always read HW values to allow filtering/debouncing to work better
        self._voltage = self._hw.read_voltage()
        self._button_state = self._hw.read_button_state()
        if self._run_count % 100 == 0:
            current_time = time.ticks_ms()
            time_passed = time.ticks_diff(current_time, self._last_run_time)
            self._last_run_time = current_time
            self.log("Battery voltage: {}; Button state: {}; Time for 100 runs: {}ms".format(
                self._voltage, self._button_state, time_passed))
        self._state.run()

    @property
    def button_pressed(self):
        return self._button_state == GrinderHardware.ButtonState.PRESSED

    @property
    def voltage(self):
        return self._voltage

    @property
    def hw(self) -> GrinderHardware:
        return self._hw
