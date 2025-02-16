import unittest

from breakn.breaker import breaker


class BreakerTestCase(unittest.TestCase):
    def test_breakn_valid_usage(self):
        @breaker
        def test_func():
            result = []
            for i in range(5):
                for j in range(5):
                    if j == 2:
                        breakn(2)
                    result.append((i, j))
            return result

        self.assertEqual(test_func(), [(0, 0), (0, 1)])

    def test_breakn_single_loop(self):
        @breaker
        def test_func():
            result = []
            for i in range(5):
                if i == 2:
                    breakn(1)
                result.append(i)
            return result

        self.assertEqual(test_func(), [0, 1])

    def test_breakn_nested_loops(self):
        @breaker
        def test_func():
            result = []
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if k == 1:
                            breakn(3)
                        result.append((i, j, k))
            return result

        self.assertEqual(test_func(), [(0, 0, 0)])

    def test_breakn_invalid_argument(self):
        with self.assertRaises(SyntaxError):

            @breaker
            def test_func():
                breakn("two")

    def test_breakn_negative_argument(self):
        with self.assertRaises(SyntaxError):

            @breaker
            def test_func():
                breakn(-1)

    def test_breakn_zero_argument(self):
        with self.assertRaises(SyntaxError):

            @breaker
            def test_func():
                breakn(0)

    def test_breakn_exceeds_loop_depth(self):
        with self.assertRaises(SyntaxError):

            @breaker
            def test_func():
                for i in range(5):
                    breakn(2)

    def test_breakn_inside_function(self):
        with self.assertRaises(SyntaxError):

            @breaker
            def test_func():
                def inner():
                    breakn(1)

                inner()

    def test_breakn_multiple_loops(self):
        @breaker
        def test_func():
            result = []
            for i in range(5):
                for j in range(5):
                    if j == 2:
                        breakn(2)
                    result.append((i, j))
            for k in range(5):
                result.append(("second", k))
            return result

        self.assertEqual(
            test_func(),
            [
                (0, 0),
                (0, 1),
                ("second", 0),
                ("second", 1),
                ("second", 2),
                ("second", 3),
                ("second", 4),
            ],
        )

    def test_breakn_try_except_handling(self):
        @breaker
        def test_func():
            result = []
            try:
                for i in range(5):
                    for j in range(5):
                        if j == 2:
                            breakn(2)
                        result.append((i, j))
            except Exception:
                result.append("exception")
            return result

        self.assertEqual(test_func(), [(0, 0), (0, 1)])


if __name__ == "__main__":
    unittest.main()
