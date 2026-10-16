import board
import espnow
import keypad
import supervisor  # pyright: ignore[reportMissingModuleSource]  (CircuitPython built-in; stubs only)
import time
import wifi
from adafruit_matrixportal.matrix import Matrix
from tt_scoreboard.gestures import DOUBLE_TAP, TAP, GestureDetector, ticks_diff
from tt_scoreboard.name_selection import NameSelection, distinct_names
from tt_scoreboard.remote_link import PRESSED, RELEASED, RemoteButtons
from tt_scoreboard.scoring import TableTennisMatch
from tt_scoreboard.screens import (
    HEIGHT,
    WIDTH,
    NameSelectDisplay,
    ScoreboardDisplay,
    WinnerDisplay,
    validate_player_names,
)

# Names must fit beside the serve markers on the scoreboard: 8 characters max.
PLAYER_NAMES = (
    "PLAYER 1",
    "PLAYER 2",
    "PLAYER 3",
    "PLAYER 4",
    "PLAYER 5",
    "PLAYER 6",
    "PLAYER 7"
)
# Available to both players, for anyone not in PLAYER_NAMES. Listed last, so a
# double tap from the start of the list reaches it.
GUEST_NAME = "GUEST"
FIRST_SERVER = 1
GAMES_TO_WIN = 4  # Best of 7

HOLD_MS = 1000
# Single taps wait this long for a possible second tap, while double taps are enabled.
DOUBLE_TAP_MS = 300
READY_PAUSE_S = 1.0
# Presses during the guard period are ignored so the winner screen is not
# skipped by accident right after the final point.
WINNER_GUARD_MS = 1500
WINNER_TIMEOUT_MS = 10000
LOOP_DELAY_S = 0.01
# Receive the wireless arcade-button remotes (the onboard buttons always work).
REMOTES_ENABLED = True
# A held remote button is forgotten if its heartbeats stop for this long.
REMOTE_TIMEOUT_MS = 500

class RemoteReceiver:
    """Receives the players' wireless button remotes over ESP-NOW."""

    def __init__(self, timeout_ms):
        wifi.radio.enabled = True
        self._espnow = espnow.ESPNow()
        self._buttons = RemoteButtons(timeout_ms)

    def poll(self, now):
        """Return (player, event) pairs, where event is PRESSED, RELEASED or LOST."""
        events = []
        packet = self._espnow.read()
        while packet is not None:
            events.extend(self._buttons.receive(packet.msg, now))
            packet = self._espnow.read()
        events.extend(self._buttons.check_timeouts(now))
        return events

    def deinit(self):
        self._espnow.deinit()

class ButtonInput:
    """Reports (player, gesture) pairs, where gesture is TAP, DOUBLE_TAP or HOLD.

    Combines the onboard UP (player 1) and DOWN (player 2) buttons with the
    optional wireless remotes. Each physical button is tracked separately.

    Double taps are only detected after clear(double_tap=True), since enabling
    them delays every single tap by double_tap_ms.
    """

    # Gesture detector keys: onboard buttons are 0 and 1, remotes 2 and 3.
    # Player number is key % 2 + 1 for both.
    _REMOTE_KEY_OFFSET = 2

    def __init__(self, hold_ms, double_tap_ms, remotes=None):
        self._keys = keypad.Keys(
            (board.BUTTON_UP, board.BUTTON_DOWN),
            value_when_pressed=False,
            pull=True,
            interval=0.03
        )
        self._remotes = remotes
        self._double_tap_ms = double_tap_ms
        self._gestures = GestureDetector(key_count=4, hold_ms=hold_ms)
        self._event = keypad.Event()

    def next_gesture(self):
        while self._keys.events.get_into(self._event):
            key = self._event.key_number
            if self._event.pressed:
                self._gestures.press(key, self._event.timestamp)
            else:
                self._gestures.release(key, self._event.timestamp)
        now = supervisor.ticks_ms()
        if self._remotes is not None:
            for player, event in self._remotes.poll(now):
                key = self._REMOTE_KEY_OFFSET + player - 1
                if event == PRESSED:
                    self._gestures.press(key, now)
                elif event == RELEASED:
                    self._gestures.release(key, now)
                else:
                    self._gestures.cancel(key)
        self._gestures.poll(now)
        detected = self._gestures.next_gesture()
        if detected is None:
            return None
        key, gesture = detected
        return key % 2 + 1, gesture

    def clear(self, double_tap=False):
        """Discard pending input, including any press still in progress."""
        self._keys.events.clear()
        if self._remotes is not None:
            self._remotes.poll(supervisor.ticks_ms())
        self._gestures.reset()
        self._gestures.double_tap_ms = self._double_tap_ms if double_tap else 0

    def deinit(self):
        self._keys.deinit()
        if self._remotes is not None:
            self._remotes.deinit()

def select_players(display, buttons):
    """Tap for the next name, double tap for the previous one, hold to lock in (or unlock)."""
    selection = NameSelection(PLAYER_NAMES + (GUEST_NAME,), shared_names=(GUEST_NAME,))
    screen = NameSelectDisplay(display)
    screen.render(selection)
    buttons.clear(double_tap=True)
    while not selection.complete:
        event = buttons.next_gesture()
        if event is not None:
            player, gesture = event
            if gesture == TAP:
                selection.cycle(player)
            elif gesture == DOUBLE_TAP:
                selection.cycle_back(player)
            else:
                selection.toggle_lock(player)
            screen.render(selection)
        time.sleep(LOOP_DELAY_S)
    time.sleep(READY_PAUSE_S)
    return distinct_names(selection.selected_names)

def play_match(display, buttons, player_names):
    """Any press awards that player a point. Returns the finished match."""
    match = TableTennisMatch(first_server=FIRST_SERVER, games_to_win=GAMES_TO_WIN)
    scoreboard = ScoreboardDisplay(display, player_names)
    scoreboard.render(match)
    buttons.clear()
    while match.winner is None:
        event = buttons.next_gesture()
        if event is not None:
            player, _ = event
            match.award_point(player)
            scoreboard.render(match)
        time.sleep(LOOP_DELAY_S)
    return match

def announce_winner(display, buttons, player_names, match):
    """Show the winner until a button is pressed or the timeout expires."""
    winner = match.winner
    WinnerDisplay(
        display,
        player_names[winner - 1],
        match.games[winner - 1],
        match.games[2 - winner],
    )
    shown_at = supervisor.ticks_ms()
    while True:
        elapsed = ticks_diff(supervisor.ticks_ms(), shown_at)
        if elapsed >= WINNER_TIMEOUT_MS:
            return
        if buttons.next_gesture() is not None and elapsed >= WINNER_GUARD_MS:
            return
        time.sleep(LOOP_DELAY_S)

def main():
    validate_player_names(PLAYER_NAMES + (GUEST_NAME,) + distinct_names((GUEST_NAME, GUEST_NAME)))
    matrix = Matrix(width=WIDTH, height=HEIGHT, bit_depth=2)
    remotes = RemoteReceiver(REMOTE_TIMEOUT_MS) if REMOTES_ENABLED else None
    buttons = ButtonInput(hold_ms=HOLD_MS, double_tap_ms=DOUBLE_TAP_MS, remotes=remotes)
    try:
        while True:
            player_names = select_players(matrix.display, buttons)
            match = play_match(matrix.display, buttons, player_names)
            announce_winner(matrix.display, buttons, player_names, match)
    finally:
        buttons.deinit()
