# from abc import ABC, abstractmethod # Not supported by MicroPython!
import time

import grinder_controller as ctrl
from grinder_hardware import GrinderHardware, AUTOGRIND_TIMEOUT_MS, AUTOGRIND_SAFETY_STOP_MS


# Should be an ABC
class State:
    _context = None

    @property
    def context(self) -> ctrl.GrinderController:
        return self._context

    @context.setter
    def context(self, c: ctrl.GrinderController):
        self._context = c

    # Should be an @abstractmethod
    def run(self) -> None:
        pass

    # Should be an @abstractmethod
    def on_enter(self) -> None:
        pass


class IdleState(State):
    def run(self):
        if self._context.button_pressed:
            self._context.state = GrindBeginState()
        elif GrinderHardware.should_start_charging(self._context.voltage):
            self._context.state = ChargingState()

    def on_enter(self):
        ctrl.GrinderController.log("Entering idle state")
        self._context.hw.set_jack_state(GrinderHardware.JackState.DISABLED)
        self._context.hw.set_motor_state(GrinderHardware.MotorState.STOPPED)


class GrindBeginState(State):
    _grind_start_time = 0

    def run(self):
        time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
        if time_passed < AUTOGRIND_TIMEOUT_MS and not self._context.button_pressed:
            self._context.state = AutoGrindState(self._grind_start_time)
        elif time_passed >= AUTOGRIND_TIMEOUT_MS:
            self._context.state = ManualGrindState()

    def on_enter(self):
        ctrl.GrinderController.log("Entering grind begin state")
        self._grind_start_time = time.ticks_ms()
        self._context.hw.set_jack_state(GrinderHardware.JackState.DISABLED)
        self._context.hw.set_motor_state(GrinderHardware.MotorState.RUNNING)


class AutoGrindState(State):
    _grind_start_time = None
    _autogrind_start_voltage = None

    def __init__(self, start_time):
        self._grind_start_time = start_time

    def run(self):
        if self._context.button_pressed:
            self._context.state = ManualGrindState()
        elif GrinderHardware.should_stop_grinding(self._context.voltage, self._autogrind_start_voltage):
            self._context.state = IdleState()
        else:
            time_passed = time.ticks_diff(time.ticks_ms(), self._grind_start_time)
            if time_passed > AUTOGRIND_SAFETY_STOP_MS:
                self._context.state = IdleState()

    def on_enter(self):
        self._autogrind_start_voltage = self._context.voltage
        ctrl.GrinderController.log("Entering automatic grinding state; Vstart={}".format(self._autogrind_start_voltage))


class ManualGrindState(State):
    def run(self):
        if not self._context.button_pressed:
            self._context.state = IdleState()

    def on_enter(self):
        ctrl.GrinderController.log("Entering manual grinding state")


class ChargingState(State):
    def run(self):
        if self._context.button_pressed:
            self._context.state = GrindBeginState()
        elif self._context.hw.should_stop_charging(self._context.voltage):
            self._context.state = IdleState()

    def on_enter(self):
        ctrl.GrinderController.log("Entering charging state")
        self._context.hw.set_motor_state(GrinderHardware.MotorState.STOPPED)
        self._context.hw.set_jack_state(GrinderHardware.JackState.ENABLED)
