import unittest

from tt_scoreboard.gestures import DOUBLE_TAP, HOLD, TAP, GestureDetector, ticks_add, ticks_diff

HOLD_MS = 1000
DOUBLE_TAP_MS = 300


class TicksDiffTest(unittest.TestCase):

    def test_simple_difference(self):
        self.assertEqual(ticks_diff(150, 100), 50)

    def test_wraparound(self):
        self.assertEqual(ticks_diff(10, (1 << 29) - 10), 20)

    def test_negative(self):
        self.assertEqual(ticks_diff(100, 150), -50)

    def test_add_wraps(self):
        self.assertEqual(ticks_add((1 << 29) - 10, 30), 20)


class DetectorTestCase(unittest.TestCase):

    def drain(self):
        gestures = []
        while True:
            gesture = self.detector.next_gesture()
            if gesture is None:
                return gestures
            gestures.append(gesture)


class GestureDetectorTest(DetectorTestCase):

    def setUp(self):
        self.detector = GestureDetector(key_count=2, hold_ms=HOLD_MS)

    def test_short_press_is_tap_on_release(self):
        self.detector.press(0, 0)
        self.detector.poll(500)
        self.assertEqual(self.drain(), [])
        self.detector.release(0, 600)
        self.assertEqual(self.drain(), [(0, TAP)])

    def test_quick_taps_are_separate_when_double_tap_disabled(self):
        for start in (0, 200):
            self.detector.press(0, start)
            self.detector.release(0, start + 50)
        self.assertEqual(self.drain(), [(0, TAP), (0, TAP)])

    def test_hold_reported_once_while_down_and_release_swallowed(self):
        self.detector.press(1, 0)
        self.detector.poll(HOLD_MS)
        self.assertEqual(self.drain(), [(1, HOLD)])
        self.detector.poll(HOLD_MS + 500)
        self.detector.release(1, HOLD_MS + 600)
        self.assertEqual(self.drain(), [])

    def test_long_press_without_poll_is_hold_on_release(self):
        self.detector.press(0, 0)
        self.detector.release(0, HOLD_MS + 1)
        self.assertEqual(self.drain(), [(0, HOLD)])

    def test_keys_are_independent(self):
        self.detector.press(0, 0)
        self.detector.press(1, 800)
        self.detector.poll(HOLD_MS)
        self.detector.release(1, 1200)
        self.assertEqual(self.drain(), [(0, HOLD), (1, TAP)])

    def test_reset_ignores_release_of_key_already_down(self):
        self.detector.press(0, 0)
        self.detector.reset()
        self.detector.poll(HOLD_MS * 2)
        self.detector.release(0, HOLD_MS * 2)
        self.assertEqual(self.drain(), [])

    def test_cancel_drops_press_without_gesture(self):
        self.detector.press(0, 0)
        self.detector.cancel(0)
        self.detector.poll(HOLD_MS * 2)
        self.detector.release(0, HOLD_MS * 2)
        self.assertEqual(self.drain(), [])

    def test_release_without_press_is_ignored(self):
        self.detector.release(0, 100)
        self.assertEqual(self.drain(), [])

    def test_rejects_invalid_timings(self):
        with self.assertRaises(ValueError):
            GestureDetector(key_count=1, hold_ms=0)
        with self.assertRaises(ValueError):
            self.detector.double_tap_ms = -1


class DoubleTapTest(DetectorTestCase):

    def setUp(self):
        self.detector = GestureDetector(
            key_count=2, hold_ms=HOLD_MS, double_tap_ms=DOUBLE_TAP_MS
        )

    def tap(self, key, start):
        self.detector.press(key, start)
        self.detector.release(key, start + 50)

    def test_single_tap_waits_for_window_to_expire(self):
        self.tap(0, 0)
        self.detector.poll(50 + DOUBLE_TAP_MS)
        self.assertEqual(self.drain(), [])
        self.detector.poll(51 + DOUBLE_TAP_MS)
        self.assertEqual(self.drain(), [(0, TAP)])

    def test_two_quick_taps_are_double_tap(self):
        self.tap(0, 0)
        self.tap(0, 200)
        self.detector.poll(1000)
        self.assertEqual(self.drain(), [(0, DOUBLE_TAP)])

    def test_second_tap_after_window_is_two_taps(self):
        self.tap(0, 0)
        self.tap(0, 50 + DOUBLE_TAP_MS + 1)
        self.detector.poll(2000)
        self.assertEqual(self.drain(), [(0, TAP), (0, TAP)])

    def test_triple_tap_is_double_tap_then_tap(self):
        for start in (0, 150, 300):
            self.tap(0, start)
        self.detector.poll(2000)
        self.assertEqual(self.drain(), [(0, DOUBLE_TAP), (0, TAP)])

    def test_tap_then_hold_is_tap_then_hold(self):
        self.tap(0, 0)
        self.detector.press(0, 200)
        self.detector.poll(200 + HOLD_MS)
        self.assertEqual(self.drain(), [(0, TAP), (0, HOLD)])

    def test_taps_on_different_keys_do_not_combine(self):
        self.tap(0, 0)
        self.tap(1, 100)
        self.detector.poll(1000)
        self.assertEqual(self.drain(), [(0, TAP), (1, TAP)])

    def test_reset_discards_pending_tap(self):
        self.tap(0, 0)
        self.detector.reset()
        self.detector.poll(1000)
        self.assertEqual(self.drain(), [])

    def test_disabling_reports_taps_immediately(self):
        self.detector.double_tap_ms = 0
        self.tap(0, 0)
        self.assertEqual(self.drain(), [(0, TAP)])


if __name__ == "__main__":
    unittest.main()
