"""Wireless button protocol shared by the remotes and the scoreboard.

Each remote is mounted at one end (side) of the table and broadcasts its
button state. Every state change bumps a counter
and is sent several times in case a packet is lost; while the button is down
the state is also repeated as a heartbeat. The scoreboard turns those messages
back into press and release events, using the counter to fill in changes whose
packets were all lost, and cancels a press whose heartbeats stop.
"""
import struct

from tt_scoreboard.gestures import ticks_add, ticks_diff

_MAGIC = 0x5454  # "TT"
_VERSION = 1
# magic, version, side (1 = left, 2 = right), session, counter, pressed
_FORMAT = ">HBBHHB"
_SIZE = struct.calcsize(_FORMAT)
_COUNTER_MASK = 0xFFFF

PRESSED = "pressed"
RELEASED = "released"
# The remote went silent while its button was down: forget the press.
LOST = "lost"


def encode(side, session, counter, pressed):
    return struct.pack(
        _FORMAT, _MAGIC, _VERSION, side, session, counter, 1 if pressed else 0
    )


def decode(message):
    """Return (side, session, counter, pressed), or None if not a valid message."""
    if len(message) != _SIZE:
        return None
    magic, version, side, session, counter, pressed = struct.unpack(_FORMAT, message)
    if magic != _MAGIC or version != _VERSION or side not in (1, 2):
        return None
    return side, session, counter, bool(pressed)


class ButtonStateSender:
    """Decides when a remote should transmit, and what."""

    def __init__(self, side, session, repeat_count=3, repeat_ms=20, heartbeat_ms=100):
        if side not in (1, 2):
            raise ValueError("Side must be 1 (left) or 2 (right)")
        self._side = side
        self._session = session & _COUNTER_MASK
        self._repeat_count = repeat_count
        self._repeat_ms = repeat_ms
        self._heartbeat_ms = heartbeat_ms
        self._counter = 0
        self._pressed = False
        self._repeats_left = 0
        self._next_at = 0

    @property
    def pressed(self):
        return self._pressed

    @property
    def idle(self):
        """True when the button is up and every repeat has been sent."""
        return not self._pressed and self._repeats_left == 0

    def set_pressed(self, pressed, now):
        if pressed == self._pressed:
            return
        self._pressed = pressed
        self._counter = (self._counter + 1) & _COUNTER_MASK
        self._repeats_left = self._repeat_count
        self._next_at = now

    def message_due(self, now):
        """Return the message to send now, or None."""
        if ticks_diff(now, self._next_at) < 0:
            return None
        if self._repeats_left > 0:
            self._repeats_left -= 1
        elif not self._pressed:
            return None
        interval = self._repeat_ms if self._repeats_left > 0 else self._heartbeat_ms
        self._next_at = ticks_add(now, interval)
        return encode(self._side, self._session, self._counter, self._pressed)


class RemoteButtonTracker:
    """Rebuilds one remote's press and release events from its messages."""

    # More missed changes than this is treated as losing track of the remote.
    _MAX_MISSED_CHANGES = 8

    def __init__(self, timeout_ms):
        self._timeout_ms = timeout_ms
        self._session = None
        self._counter = 0
        self._pressed = False
        self._last_seen = 0

    def update(self, session, counter, pressed, now):
        """Return the events (PRESSED, RELEASED, LOST) implied by a message."""
        self._last_seen = now
        if session == self._session:
            changes = (counter - self._counter) & _COUNTER_MASK
            if changes == 0 or changes > _COUNTER_MASK // 2:
                return []  # Repeat, heartbeat, or out-of-order packet.
            if changes <= self._MAX_MISSED_CHANGES:
                events = []
                state = self._pressed
                for _ in range(changes):
                    state = not state
                    events.append(PRESSED if state else RELEASED)
                if state == pressed:
                    self._counter = counter
                    self._pressed = pressed
                    return events
        return self._resync(session, counter, pressed)

    def check_timeout(self, now):
        """Return LOST if a press has gone without a heartbeat for too long."""
        if self._pressed and ticks_diff(now, self._last_seen) > self._timeout_ms:
            self._pressed = False
            return LOST
        return None

    def _resync(self, session, counter, pressed):
        # A new session means the remote restarted, or the scoreboard did. A
        # press still in progress is real (it is usually the first press since
        # the scoreboard started), but any press we were tracking is stale.
        events = [LOST] if self._pressed else []
        if pressed:
            events.append(PRESSED)
        self._session = session
        self._counter = counter
        self._pressed = pressed
        return events


class RemoteButtons:
    """Tracks the remotes at both ends of the table from raw received messages."""

    def __init__(self, timeout_ms):
        self._trackers = (RemoteButtonTracker(timeout_ms), RemoteButtonTracker(timeout_ms))

    def receive(self, message, now):
        """Return (side, event) pairs for one received message."""
        decoded = decode(message)
        if decoded is None:
            return []
        side, session, counter, pressed = decoded
        events = self._trackers[side - 1].update(session, counter, pressed, now)
        return [(side, event) for event in events]

    def check_timeouts(self, now):
        """Return (side, LOST) pairs for remotes that went silent mid-press."""
        lost = []
        for index, tracker in enumerate(self._trackers):
            if tracker.check_timeout(now) is not None:
                lost.append((index + 1, LOST))
        return lost
