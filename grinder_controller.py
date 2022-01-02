from abc import ABC, abstractmethod
from enum import Enum
import time


AUTOGRIND_TIMEOUT_MS = 1000
AUTOGRIND_SAFETY_STOP_MS = 1000 * 60


class GrinderController:
    class ButtonState(Enum):
        PRESSED = 0
        RELEASED = 1

    class JackState(Enum):
        ENABLED = 0
        DISABLED = 1

    class MotorState(Enum):
        RUNNING = 0
        STOPPED = 1

    class State(ABC):
        _context = None

        @property
        def context(self):
            return self._context

        @context.setter
        def context(self, c):
            self._context = c

        @abstractmethod
        def run(self):
            pass

        @abstractmethod
        def on_enter(self):
            pass

    class IdleState(State):
        def run(self):
            if self._context.button_state == GrinderController.ButtonState.PRESSED:
                self._context.state = GrinderController.GrindBeginState()
            elif self._context.hw.should_start_charging(self._context.voltage):
                self._context.state = GrinderController.ChargingState()

        def on_enter(self):
            print("Entering idle state")
            self._context.hw.set_jack_state(GrinderController.JackState.DISABLED)
            self._context.hw.set_motor_state(GrinderController.MotorState.STOPPED)

    class GrindBeginState(State):
        _grind_start_time = None

        def run(self):
            time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
            if time_passed < AUTOGRIND_TIMEOUT_MS and \
                    self._context.button_state == GrinderController.ButtonState.RELEASED:
                self._context.state = GrinderController.AutoGrindState(self._grind_start_time)
            elif time_passed >= AUTOGRIND_TIMEOUT_MS:
                self._context.state = GrinderController.ManualGrindState()

        def on_enter(self):
            print("Entering grind begin state")
            self._grind_start_time = time.ticks_ms()
            self._context.hw.set_jack_state(GrinderController.JackState.DISABLED)
            self._context.hw.set_motor_state(GrinderController.MotorState.RUNNING)

    class AutoGrindState(State):
        _grind_start_time = None
        _autogrind_start_voltage = None

        def __init__(self, start_time):
            self._grind_start_time = start_time

        def run(self):
            time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
            if self._context.button_state == GrinderController.ButtonState.PRESSED:
                self._context.state = GrinderController.AutoGrindStopState()
            elif time_passed > AUTOGRIND_SAFETY_STOP_MS:
                self._context.state = GrinderController.IdleState()
            elif self._context.hw.should_stop_grinding(self._context.voltage, self._autogrind_start_voltage):
                self._context.state = GrinderController.IdleState()

        def on_enter(self):
            print("Entering automatic grinding state")
            self._autogrind_start_voltage = self._context.voltage()

    class AutoGrindStopState(State):
        def run(self):
            if self._context.button_state == GrinderController.ButtonState.RELEASED:
                self._context.state = GrinderController.IdleState()

        def on_enter(self):
            print("Entering automatic grinding stop state")
            self._context.hw.set_motor_state(GrinderController.MotorState.STOPPED)

    class ManualGrindState(State):
        def run(self):
            if self._context.button_state == GrinderController.ButtonState.RELEASED:
                self._context.state = GrinderController.IdleState()

        def on_enter(self):
            print("Entering manual grinding state")

    class ChargingState(State):
        def run(self):
            if self._context.button_state == GrinderController.ButtonState.PRESSED:
                self._context.state = GrinderController.GrindBeginState()
            if self._context.hw.should_stop_charging(self._context.voltage):
                self._context.state = GrinderController.IdleState()

        def on_enter(self):
            print("Entering charging state")
            self._context.hw.set_motor_state(GrinderController.MotorState.STOPPED)
            self._context.hw.set_jack_state(GrinderController.JackState.ENABLED)

    _state = None
    _hw = None
    _button_state = None
    _voltage = None

    def __init__(self, hw):
        self._hw = hw
        self.state = GrinderController.IdleState()

    def run(self):
        self._voltage = self._hw.read_voltage()
        self._button_state = self._hw.read_button_state()
        print("Battery voltage: {}; Button state: {}".format(self._voltage, self._button_state))
        self._state.run()

    @property
    def button_state(self):
        return self._button_state

    @property
    def voltage(self):
        return self._voltage

    @property
    def hw(self):
        return self._hw

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self._state.context = self
        self._state.on_enter()
