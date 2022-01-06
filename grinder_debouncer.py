import time


class GrinderDebouncer:
    def __init__(self, initial_value: int, debounce_time_ms: int):
        self._prev_button_state = initial_value
        self._button_change_time = time.ticks_ms()
        self._debounced_button_state = initial_value
        self._debounce_time_ms = debounce_time_ms

    def debounce_button(self, pin_state: int) -> int:
        if pin_state != self._prev_button_state:
            self._prev_button_state = pin_state
            self._button_change_time = time.ticks_ms()
        elif pin_state != self._debounced_button_state:
            time_passed = time.ticks_diff(time.ticks_ms(), self._button_change_time)
            if time_passed > self._debounce_time_ms:
                self._debounced_button_state = pin_state

        return self._debounced_button_state
