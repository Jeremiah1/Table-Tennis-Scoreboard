"""Simulated play through the SWITCH SIDES message in the deciding game.

Runs the real app.play_match with fake buttons, remotes and display, on a
virtual clock, and checks what the board shows after each scripted press.
"""
import sys
import types
import unittest
from unittest import mock


# ---- Stand-ins for the CircuitPython modules app.py and screens.py import ----

class _Clock:
    now = 0


CLOCK = _Clock()


class _Group(list):
    def __init__(self, **kwargs):
        super().__init__()
        self.hidden = False


class _Label:
    CHAR_WIDTH = 6

    def __init__(self, font, text="", scale=1, anchored_position=(0, 0), **kwargs):
        self.text = text
        self.scale = scale
        self.hidden = False
        width = self.CHAR_WIDTH * len(text)
        self.bounding_box = (0, 0, width, 8)
        self.x = anchored_position[0] - width // 2
        self.y = anchored_position[1]


class _Rectangle:
    def __init__(self, **kwargs):
        self.hidden = False


class _Palette(list):
    def __init__(self, count):
        super().__init__([0] * count)


class _KeyEvent:
    def __init__(self):
        self.key_number = 0
        self.pressed = False
        self.timestamp = 0


class _KeyEvents:
    """keypad's event queue, fed from a script of (time, key, pressed)."""

    def __init__(self):
        self.script = []

    def _due(self):
        return [event for event in self.script if event[0] <= CLOCK.now]

    def get_into(self, event):
        due = self._due()
        if not due:
            return False
        self.script.remove(due[0])
        event.timestamp, event.key_number, event.pressed = due[0]
        return True

    def clear(self):
        for event in self._due():
            self.script.remove(event)


class _Keys:
    def __init__(self, *args, **kwargs):
        self.events = _KeyEvents()

    def deinit(self):
        pass


def _install_fake_modules():
    fakes = {
        "board": {"BUTTON_UP": 0, "BUTTON_DOWN": 1},
        "displayio": {"Group": _Group, "Palette": _Palette},
        "terminalio": {"FONT": None},
        "vectorio": {"Rectangle": _Rectangle},
        "adafruit_display_text": {},
        "adafruit_display_text.label": {"Label": _Label},
        "keypad": {"Keys": _Keys, "Event": _KeyEvent},
        "supervisor": {"ticks_ms": lambda: CLOCK.now},
        "espnow": {},
        "wifi": {},
        "microcontroller": {},
        "adafruit_matrixportal": {},
        "adafruit_matrixportal.matrix": {"Matrix": None},
    }
    for name, attributes in fakes.items():
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__dict__.update(attributes)
            sys.modules[name] = module
    sys.modules["adafruit_display_text"].label = sys.modules["adafruit_display_text.label"]


_install_fake_modules()

from tt_scoreboard import app, screens  # noqa: E402
from tt_scoreboard.remote_link import PRESSED, RELEASED  # noqa: E402
from tt_scoreboard.scoring import LEFT, RIGHT, TableTennisMatch, games_to_win  # noqa: E402

NAMES = ("ALICE", "BOB")
SWITCH_MESSAGE = ("SWITCH", "SIDES")
TAP_MS = 80


class _Remotes:
    """Wireless remotes, fed from a script of (time, side, PRESSED or RELEASED)."""

    def __init__(self):
        self.script = []

    def poll(self, now):
        due = [event for event in self.script if event[0] <= now]
        for event in due:
            self.script.remove(event)
        return [(side, event) for _, side, event in due]

    def battery(self, side):
        return None

    def deinit(self):
        pass


class _Display:
    root_group = None


class _SimulationOver(Exception):
    pass


class _Simulation:
    """Plays a match from a script of presses and records each screen shown."""

    def __init__(self, match, presses, remotes=True):
        """presses: (time_ms, side, duration_ms) tuples."""
        self.match = match
        self.display = _Display()
        self.board = None
        self.screens = []
        remote_input = _Remotes() if remotes else None
        self.buttons = app.ButtonInput(
            hold_ms=app.HOLD_MS, double_tap_ms=app.DOUBLE_TAP_MS, remotes=remote_input
        )
        for start, side, duration in presses:
            if remotes:
                remote_input.script += [(start, side, PRESSED), (start + duration, side, RELEASED)]
            else:
                self.buttons._keys.events.script += [
                    (start, side - 1, True), (start + duration, side - 1, False)
                ]
        self.end = max(start + duration for start, _, duration in presses) + 1500

    def run(self):
        simulation = self

        class RecordingScoreboard(screens.ScoreboardDisplay):
            def __init__(self, display, player_names):
                super().__init__(display, player_names)
                simulation.board = self

        CLOCK.now = 0
        fake_time = types.SimpleNamespace(sleep=self._sleep)
        with mock.patch.object(app, "ScoreboardDisplay", RecordingScoreboard), \
                mock.patch.object(app, "time", fake_time):
            try:
                app.play_match(self.display, self.buttons, NAMES, self.match)
            except _SimulationOver:
                pass
        self._record()
        return self

    def _sleep(self, seconds):
        self._record()
        CLOCK.now += max(1, int(seconds * 1000))
        if CLOCK.now > self.end:
            raise _SimulationOver

    def _record(self):
        screen = self._describe()
        if not self.screens or self.screens[-1] != screen:
            self.screens.append(screen)

    def _describe(self):
        """("board", left, right) with (name, score, serving) per side, or the message lines."""
        root = self.display.root_group
        if self.board is not None and root is self.board._root:
            sides = []
            for side in range(2):
                for header, markers in self.board._headers[side]:
                    if not header.hidden:
                        sides.append((header[0].text, int(self.board._scores[side].text),
                                      not markers.hidden))
            return ("board",) + tuple(sides)
        return tuple(item.text for item in root if isinstance(item, _Label))[:2]


def deciding_game(points_1, points_2, first_server=1, best_of=7):
    """A match at the start of its deciding game, then the given points in it."""
    match = TableTennisMatch(first_server=first_server, games_to_win=games_to_win(best_of))
    for _ in range(games_to_win(best_of) - 1):
        for player in (1, 2):
            while match.award_point(player) != player:
                pass
    for _ in range(points_1):
        match.award_point(1)
    for _ in range(points_2):
        match.award_point(2)
    return match


def board(left, right):
    return ("board", left, right)


class SwitchSidesTest(unittest.TestCase):
    """ALICE is player 1 and starts the deciding game at the left end."""

    def play(self, match, presses, remotes=True):
        return _Simulation(match, presses, remotes).run()

    def test_fifth_point_asks_to_switch_and_tap_dismisses_without_scoring(self):
        sim = self.play(deciding_game(4, 3), [(1000, LEFT, TAP_MS), (3000, RIGHT, TAP_MS)])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 3, True)),
            SWITCH_MESSAGE,
            board(("BOB", 3, False), ("ALICE", 5, True)),
        ])
        self.assertEqual(sim.match.points, (5, 3))

    def test_either_remote_dismisses(self):
        sim = self.play(deciding_game(4, 3), [(1000, LEFT, TAP_MS), (3000, LEFT, TAP_MS)])
        self.assertEqual(sim.screens[-1], board(("BOB", 3, False), ("ALICE", 5, True)))
        self.assertEqual(sim.match.points, (5, 3))

    def test_onboard_buttons_work_the_same(self):
        sim = self.play(deciding_game(3, 4), [(1000, RIGHT, TAP_MS), (3000, LEFT, TAP_MS)],
                        remotes=False)
        self.assertEqual(sim.screens, [
            board(("ALICE", 3, False), ("BOB", 4, True)),
            SWITCH_MESSAGE,
            board(("BOB", 5, False), ("ALICE", 3, True)),
        ])

    def test_remotes_score_for_the_player_now_at_their_end(self):
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, RIGHT, TAP_MS),
            (6000, LEFT, TAP_MS),  # BOB now stands at the left end.
        ])
        self.assertEqual(sim.match.points, (5, 4))
        self.assertEqual(sim.screens[-1], board(("BOB", 4, False), ("ALICE", 5, True)))

    def test_server_follows_the_player_when_bob_served_first(self):
        sim = self.play(deciding_game(4, 4, first_server=2),
                        [(1000, LEFT, TAP_MS), (3000, LEFT, TAP_MS)])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 4, True)),
            SWITCH_MESSAGE,
            board(("BOB", 4, True), ("ALICE", 5, False)),
        ])

    def test_best_of_five_deciding_game(self):
        sim = self.play(deciding_game(4, 2, best_of=5),
                        [(1000, LEFT, TAP_MS), (3000, RIGHT, TAP_MS)])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 2, True)),
            SWITCH_MESSAGE,
            board(("BOB", 2, True), ("ALICE", 5, False)),
        ])

    def test_tap_before_the_message_appears_is_discarded(self):
        # The scoring tap is held back DOUBLE_TAP_MS for a possible double tap,
        # and a tap at the other end in that time is dropped with the message.
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (1230, RIGHT, TAP_MS), (3000, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.screens[-1], board(("BOB", 3, False), ("ALICE", 5, True)))
        self.assertEqual(sim.match.points, (5, 3))

    def test_both_players_tapping_the_message_dismisses_it_once(self):
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, LEFT, TAP_MS), (3200, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.match.points, (5, 3))

    def test_hold_on_the_message_is_ignored(self):
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, RIGHT, 1200), (6000, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 3, True)),
            SWITCH_MESSAGE,
            board(("BOB", 3, False), ("ALICE", 5, True)),
        ])
        self.assertEqual(sim.match.points, (5, 3))

    def test_double_tap_on_the_message_undoes_the_point_without_switching(self):
        # Two quick taps on the message are a double tap: the 5th point is
        # undone and the unswapped board returns, with no message about it.
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, RIGHT, TAP_MS), (3280, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 3, True)),
            SWITCH_MESSAGE,
            board(("ALICE", 4, False), ("BOB", 3, True)),
        ])
        self.assertEqual(sim.match.points, (4, 3))

    def test_undo_on_the_swapped_board_asks_to_switch_again(self):
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, RIGHT, TAP_MS),
            (5000, RIGHT, TAP_MS), (5150, RIGHT, TAP_MS),  # Double tap: undo.
            (7000, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.screens, [
            board(("ALICE", 4, False), ("BOB", 3, True)),
            SWITCH_MESSAGE,
            board(("BOB", 3, False), ("ALICE", 5, True)),
            SWITCH_MESSAGE,
            board(("ALICE", 4, False), ("BOB", 3, True)),
        ])
        self.assertEqual(sim.match.points, (4, 3))

    def test_tap_after_the_message_closes_scores(self):
        # Once the board is back, a tap is a point like any other.
        sim = self.play(deciding_game(4, 3), [
            (1000, LEFT, TAP_MS), (3000, LEFT, TAP_MS), (3450, RIGHT, TAP_MS),
        ])
        self.assertEqual(sim.match.points, (6, 3))
        self.assertEqual(sim.screens[-1], board(("BOB", 3, False), ("ALICE", 6, True)))


if __name__ == "__main__":
    unittest.main()
