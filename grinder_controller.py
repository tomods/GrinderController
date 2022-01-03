from grinder_controller_states import *
from grinder_hardware import GrinderHardware


class GrinderController:
    def __init__(self, hw: GrinderHardware):
        self._hw = hw
        self._voltage = 0
        self._button_state = GrinderHardware.ButtonState.RELEASED
        self._state = IdleState()  # init only
        self.state = self._state  # call setter

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, state: State):
        self._state = state
        self._state.context = self
        self._state.on_enter()

    def run(self):
        # Always read HW values to allow filtering/debouncing to work better
        self._voltage = self._hw.read_voltage()
        self._button_state = self._hw.read_button_state()
        print("Battery voltage: {}; Button state: {}".format(self._voltage, self._button_state))
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
