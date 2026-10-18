import board
import espnow
import keypad
import supervisor  # pyright: ignore[reportMissingModuleSource]  (CircuitPython built-in; stubs only)
import time
import wifi
from adafruit_matrixportal.matrix import Matrix
from tt_scoreboard.gestures import DOUBLE_TAP, HOLD, TAP, GestureDetector, ticks_diff
from tt_scoreboard.name_selection import NameSelection, distinct_names
from tt_scoreboard.remote_link import PRESSED, RELEASED, RemoteButtons
from tt_scoreboard.scoring import TableTennisMatch
from tt_scoreboard.screens import (
    HEIGHT,
    WIDTH,
    NameSelectDisplay,
    ScoreboardDisplay,
    ServeSelectDisplay,
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
GAMES_TO_WIN = 4  # Best of 7

HOLD_MS = 1000
# Single taps wait this long for a possible second tap, while double taps are enabled.
DOUBLE_TAP_MS = 300
READY_PAUSE_S = 1.0
WINNER_TIMEOUT_MS = 30000
LOOP_DELAY_S = 0.01
# Receive the wireless arcade-button remotes (the onboard buttons always work).
REMOTES_ENABLED = True
# A held remote button is forgotten if its heartbeats stop for this long.
REMOTE_TIMEOUT_MS = 500

class RemoteReceiver:
    """Receives the wireless button remotes at each end of the table over ESP-NOW."""

    def __init__(self, timeout_ms):
        wifi.radio.enabled = True
        self._espnow = espnow.ESPNow()
        self._buttons = RemoteButtons(timeout_ms)

    def poll(self, now):
        """Return (side, event) pairs, where event is PRESSED, RELEASED or LOST."""
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
    """Reports (side, gesture) pairs, where side is LEFT or RIGHT and gesture
    is TAP, DOUBLE_TAP or HOLD.

    Combines the onboard UP (left) and DOWN (right) buttons with the optional
    wireless remotes. Each physical button is tracked separately.

    Double taps are only detected after clear(double_tap=True), since enabling
    them delays every single tap by double_tap_ms.
    """

    # Gesture detector keys: onboard buttons are 0 and 1, remotes 2 and 3.
    # The side is key % 2 + 1 for both.
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
            for side, event in self._remotes.poll(now):
                key = self._REMOTE_KEY_OFFSET + side - 1
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
    """Tap for the next name, double tap for the previous one, hold to lock in (or unlock).

    The left button picks player 1, who starts at the left end.
    """
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

def select_server(display, buttons, player_names):
    """Tap your button to serve first, then hold either button to start.

    Returns the player who serves first.
    """
    screen = ServeSelectDisplay(display, player_names)
    server = None
    screen.render(server)
    buttons.clear()
    while True:
        event = buttons.next_gesture()
        if event is not None:
            side, gesture = event
            if gesture == HOLD:
                if server is not None:
                    return server
            else:
                # Player 1 starts on the left, so the side is the player.
                server = side
                screen.render(server)
        time.sleep(LOOP_DELAY_S)

def play_match(display, buttons, player_names, match):
    """Play until the match has a winner.

    A press awards a point to the player at that end of the table, and a
    double tap on either button undoes the last point.
    """
    scoreboard = ScoreboardDisplay(display, player_names)
    scoreboard.render(match)
    buttons.clear(double_tap=True)
    while match.winner is None:
        event = buttons.next_gesture()
        if event is not None:
            side, gesture = event
            if gesture == DOUBLE_TAP:
                if match.can_undo:
                    match.undo_last_point()
            else:
                match.award_point(match.player_on_side(side))
            scoreboard.render(match)
        time.sleep(LOOP_DELAY_S)

def announce_winner(display, buttons, player_names, match):
    """Show the winner until a button is held or the timeout expires.

    Taps are ignored, so a double tap that comes out as a single tap does not
    skip the screen. Returns True if a double tap undid the winning point, so
    play resumes.
    Input is not cleared on entry, so a double tap that began on the
    scoreboard still counts.
    """
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
            return False
        event = buttons.next_gesture()
        if event is not None:
            _, gesture = event
            if gesture == DOUBLE_TAP:
                match.undo_last_point()
                return True
            if gesture == HOLD:
                return False
        time.sleep(LOOP_DELAY_S)

def main():
    validate_player_names(PLAYER_NAMES + (GUEST_NAME,) + distinct_names((GUEST_NAME, GUEST_NAME)))
    matrix = Matrix(width=WIDTH, height=HEIGHT, bit_depth=2)
    remotes = RemoteReceiver(REMOTE_TIMEOUT_MS) if REMOTES_ENABLED else None
    buttons = ButtonInput(hold_ms=HOLD_MS, double_tap_ms=DOUBLE_TAP_MS, remotes=remotes)
    try:
        while True:
            player_names = select_players(matrix.display, buttons)
            first_server = select_server(matrix.display, buttons, player_names)
            match = TableTennisMatch(first_server=first_server, games_to_win=GAMES_TO_WIN)
            while True:
                play_match(matrix.display, buttons, player_names, match)
                if not announce_winner(matrix.display, buttons, player_names, match):
                    break
    finally:
        buttons.deinit()
