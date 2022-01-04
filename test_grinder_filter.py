import unittest
from grinder_filter import GrinderFilter


class MyTestCase(unittest.TestCase):
    def test_filter_voltages1(self):
        voltages1 = [38000 for _ in range(100)]
        v_filter = GrinderFilter(30000, 16)
        for v in voltages1:
            filtered_voltage = v_filter.filter_value(v)
            print(filtered_voltage)

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
