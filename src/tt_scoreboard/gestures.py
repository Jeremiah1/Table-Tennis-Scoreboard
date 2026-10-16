TAP = "tap"
DOUBLE_TAP = "double_tap"
HOLD = "hold"

# supervisor.ticks_ms() and keypad timestamps wrap around at 2**29.
_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALF_PERIOD = _TICKS_PERIOD // 2


def ticks_diff(end, start):
    """Milliseconds from start to end, tolerant of tick counter wraparound."""
    diff = (end - start) & _TICKS_MAX
    if diff >= _TICKS_HALF_PERIOD:
        diff -= _TICKS_PERIOD
    return diff


class GestureDetector:
    """Classifies raw press/release events into taps, double taps and holds.

    Feed it press(), release() and regular poll() calls, then drain detected
    (key, gesture) pairs with next_gesture().

    A hold is reported as soon as the key has been down for hold_ms, without
    waiting for release, and the release that follows it is swallowed.

    While double_tap_ms is 0, a shorter press is reported as a tap on release.
    Otherwise a tap is held back until double_tap_ms passes with no new press,
    and a second short press inside that window is reported as a double tap.
    """

    def __init__(self, key_count, hold_ms, double_tap_ms=0):
        if hold_ms <= 0:
            raise ValueError("Hold time must be positive")
        self._hold_ms = hold_ms
        self.double_tap_ms = double_tap_ms
        self._pressed_at = [None] * key_count
        self._held = [False] * key_count
        self._tap_released_at = [None] * key_count
        self._gestures = []

    @property
    def double_tap_ms(self):
        return self._double_tap_ms

    @double_tap_ms.setter
    def double_tap_ms(self, value):
        if value < 0:
            raise ValueError("Double tap time must not be negative")
        self._double_tap_ms = value

    def press(self, key, now):
        released_at = self._tap_released_at[key]
        if released_at is not None and ticks_diff(now, released_at) > self._double_tap_ms:
            self._flush_tap(key)
        self._pressed_at[key] = now
        self._held[key] = False

    def release(self, key, now):
        pressed_at = self._pressed_at[key]
        held = self._held[key]
        self._pressed_at[key] = None
        self._held[key] = False
        if pressed_at is None or held:
            return
        if ticks_diff(now, pressed_at) >= self._hold_ms:
            # poll() did not run while the key crossed the hold threshold.
            self._report_hold(key)
        elif not self._double_tap_ms:
            self._gestures.append((key, TAP))
        elif self._tap_released_at[key] is not None:
            self._tap_released_at[key] = None
            self._gestures.append((key, DOUBLE_TAP))
        else:
            self._tap_released_at[key] = now

    def poll(self, now):
        """Report holds and taps whose double tap window has expired."""
        for key, pressed_at in enumerate(self._pressed_at):
            if pressed_at is None:
                released_at = self._tap_released_at[key]
                if released_at is not None and ticks_diff(now, released_at) > self._double_tap_ms:
                    self._flush_tap(key)
            elif not self._held[key] and ticks_diff(now, pressed_at) >= self._hold_ms:
                self._held[key] = True
                self._report_hold(key)

    def next_gesture(self):
        """Return the oldest undelivered (key, gesture) pair, or None."""
        if self._gestures:
            return self._gestures.pop(0)
        return None

    def reset(self):
        """Forget pending gestures and keys currently down.

        The eventual release of a key that is down now is ignored.
        """
        for key in range(len(self._pressed_at)):
            self._pressed_at[key] = None
            self._held[key] = False
            self._tap_released_at[key] = None
        self._gestures = []

    def _flush_tap(self, key):
        self._tap_released_at[key] = None
        self._gestures.append((key, TAP))

    def _report_hold(self, key):
        # A tap waiting on a possible double tap happened first.
        if self._tap_released_at[key] is not None:
            self._flush_tap(key)
        self._gestures.append((key, HOLD))
