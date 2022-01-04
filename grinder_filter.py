from collections import deque


# Smoothing filter for ADC values to try and get rid of some noise.
# Just implements SMA as per
# [https://en.wikipedia.org/w/index.php?title=Moving_average&oldid=1060117206#Simple_moving_average].
#
# Tries to optimize for microcontrollers by not using floating point arithmetic.
# Best suited for values of 16 bit and less -- internally shifts left by 16 bits to avoid rounding/truncation issues.
class GrinderFilter:
    def __init__(self, initial_value: int, filter_size):
        self._filter_deque = deque(tuple(), filter_size)
        for _ in range(filter_size):
            self._filter_deque.append(initial_value)
        self._value_filtered = initial_value << 16
        self._filter_size = filter_size

    def filter_value(self, new_val: int) -> int:
        oldest = self._filter_deque.popleft()
        self._filter_deque.append(new_val)
        # Shift around a bit to avoid losing accuracy without using floating point arithmetic
        self._value_filtered += ((new_val - oldest) << 16) // self._filter_size

        return int(self._value_filtered >> 16)
