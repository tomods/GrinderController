from collections import deque


class GrinderFilter:
    def __init__(self, initial_value: int, filter_size):
        self._filter_deque = deque(tuple(), filter_size)
        for _ in range(filter_size):
            self._filter_deque.append(initial_value)
        self._value_filtered = initial_value
        self._filter_size = filter_size

    def filter_value(self, new_val: int) -> int:
        oldest = self._filter_deque.popleft()
        self._filter_deque.append(new_val)
        # TODO: Avoid floating point math.
        #       But DO NOT just use integer division - will introduce too much error!
        self._value_filtered += (new_val - oldest) / self._filter_size

        return int(self._value_filtered)
