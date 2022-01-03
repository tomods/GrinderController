from abc import ABC, abstractmethod
import time

from grinder_controller import GrinderController
from grinder_hardware import GrinderHardware, AUTOGRIND_TIMEOUT_MS, AUTOGRIND_SAFETY_STOP_MS


class State(ABC):
    _context = None

    @property
    def context(self) -> GrinderController:
        return self._context

    @context.setter
    def context(self, c: GrinderController):
        self._context = c

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def on_enter(self) -> None:
        pass


class IdleState(State):
    def run(self):
        if self._context.button_state == GrinderHardware.ButtonState.PRESSED:
            self._context.state = GrindBeginState()
        elif self._context.hw.should_start_charging(self._context.voltage):
            self._context.state = ChargingState()

    def on_enter(self):
        print("Entering idle state")
        self._context.hw.set_jack_state(GrinderHardware.JackState.DISABLED)
        self._context.hw.set_motor_state(GrinderHardware.MotorState.STOPPED)


class GrindBeginState(State):
    _grind_start_time = 0

    def run(self):
        time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
        if time_passed < AUTOGRIND_TIMEOUT_MS and \
                self._context.button_state == GrinderHardware.ButtonState.RELEASED:
            self._context.state = AutoGrindState(self._grind_start_time)
        elif time_passed >= AUTOGRIND_TIMEOUT_MS:
            self._context.state = ManualGrindState()

    def on_enter(self):
        print("Entering grind begin state")
        self._grind_start_time = time.ticks_ms()
        self._context.hw.set_jack_state(GrinderHardware.JackState.DISABLED)
        self._context.hw.set_motor_state(GrinderHardware.MotorState.RUNNING)


class AutoGrindState(State):
    _grind_start_time = None
    _autogrind_start_voltage = None

    def __init__(self, start_time):
        self._grind_start_time = start_time

    def run(self):
        if self._context.button_state == GrinderHardware.ButtonState.PRESSED:
            self._context.state = AutoGrindStopState()
        elif self._context.hw.should_stop_grinding(self._context.voltage, self._autogrind_start_voltage):
            self._context.state = IdleState()
        else:
            time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
            if time_passed > AUTOGRIND_SAFETY_STOP_MS:
                self._context.state = IdleState()

    def on_enter(self):
        print("Entering automatic grinding state")
        self._autogrind_start_voltage = self._context.voltage()


class AutoGrindStopState(State):
    def run(self):
        if self._context.button_state == GrinderHardware.ButtonState.RELEASED:
            self._context.state = IdleState()

    def on_enter(self):
        print("Entering automatic grinding stop state")
        self._context.hw.set_motor_state(GrinderHardware.MotorState.STOPPED)


class ManualGrindState(State):
    def run(self):
        if self._context.button_state == GrinderHardware.ButtonState.RELEASED:
            self._context.state = IdleState()

    def on_enter(self):
        print("Entering manual grinding state")


class ChargingState(State):
    def run(self):
        if self._context.button_state == GrinderHardware.ButtonState.PRESSED:
            self._context.state = GrindBeginState()
        elif self._context.hw.should_stop_charging(self._context.voltage):
            self._context.state = IdleState()

    def on_enter(self):
        print("Entering charging state")
        self._context.hw.set_motor_state(GrinderHardware.MotorState.STOPPED)
        self._context.hw.set_jack_state(GrinderHardware.JackState.ENABLED)
