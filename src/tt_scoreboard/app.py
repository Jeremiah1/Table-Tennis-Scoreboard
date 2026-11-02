import board
import espnow
import keypad
import microcontroller
import os
import supervisor  # pyright: ignore[reportMissingModuleSource]  (CircuitPython built-in; stubs only)
import time
import wifi
from adafruit_matrixportal.matrix import Matrix
from tt_scoreboard.crash_log import SIZE as CRASH_LOG_SIZE, CrashLog
from tt_scoreboard.gestures import DOUBLE_TAP, HOLD, TAP, GestureDetector, ticks_diff
from tt_scoreboard.name_selection import NameSelection, distinct_names, parse_player_names
from tt_scoreboard.remote_link import PRESSED, RELEASED, RemoteButtons
from tt_scoreboard.scoring import TableTennisMatch, games_to_win
from tt_scoreboard.screens import (
    HALF_CHARS,
    HEIGHT,
    LEADERBOARD_ROWS,
    ERROR_COLOR,
    WIDTH,
    WINNER_COLOR,
    LeaderboardDisplay,
    MessageDisplay,
    NameSelectDisplay,
    PlayerCardDisplay,
    ScoreboardDisplay,
    ServeSelectDisplay,
    WinnerDisplay,
    validate_player_names,
)
from tt_scoreboard.stats import NvmStore, StatsBook, summary

# Names must fit beside the serve markers on the scoreboard: 8 characters max.
# They come from TT_PLAYERS in the board's settings.toml (a comma-separated
# list, written by deploy.sh from players.txt), so they stay out of the code.
PLAYER_NAMES = parse_player_names(
    os.getenv("TT_PLAYERS"),
    default=("PLAYER 1", "PLAYER 2", "PLAYER 3", "PLAYER 4"),
)
# Available to both players, for anyone not in PLAYER_NAMES. Guests have no stats.
GUEST_NAME = "GUEST"
# Menu entry at the end of the name list (a double tap from the start reaches
# it); hold on it to browse the stats.
STATS_ENTRY = "STATS"
# Match lengths offered on the serve screen (double tap to change), and the
# one the board starts with. The last choice is kept until the board restarts.
BEST_OF_CHOICES = (7, 5)
DEFAULT_BEST_OF = 7

HOLD_MS = 1000
# Single taps wait this long for a possible second tap, while double taps are enabled.
DOUBLE_TAP_MS = 300
READY_PAUSE_S = 1.0
WINNER_TIMEOUT_MS = 30000
# A player's stats replace HOLD=LOCK once their cursor rests on a name this long.
NAME_STATS_DELAY_MS = 1000
# The name screen starts cycling through the stats after this long untouched.
IDLE_STATS_MS = 60000
# How long each page shows while stats cycle by themselves.
LEADERBOARD_PAGE_MS = 6000
CARD_PAGE_MS = 5000
# Browsing stats returns to the name screen after this long untouched.
STATS_BROWSE_TIMEOUT_MS = 60000
# Hold both buttons this long on a stats screen to ask about a reset, then this
# long again to confirm it.
RESET_HOLD_MS = 5000
RESET_CONFIRM_HOLD_MS = 3000
RESET_CONFIRM_TIMEOUT_MS = 15000
LOOP_DELAY_S = 0.01
# This panel has its red and blue channels swapped; "RGB" for a standard panel.
MATRIX_COLOR_ORDER = "BGR"
# Receive the wireless arcade-button remotes (the onboard buttons always work).
REMOTES_ENABLED = True
# A held remote button is forgotten if its heartbeats stop for this long.
REMOTE_TIMEOUT_MS = 500
# After a crash the board shows ERROR this long, then restarts, unless it had
# run for less than CRASH_RESTART_MIN_UPTIME_S. The report is saved either way.
CRASH_MESSAGE_S = 5
CRASH_RESTART_MIN_UPTIME_S = 60

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

    def battery(self, side):
        """The side's remote battery charge in percent, or None if not reported yet."""
        return self._buttons.battery(side)

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

    def held_ms(self, side):
        """How long the side's button has been down, or 0.

        The longest of the side's onboard and remote buttons. Only up to date
        as of the last next_gesture() call.
        """
        now = supervisor.ticks_ms()
        return max(
            self._gestures.held_ms(side - 1, now),
            self._gestures.held_ms(self._REMOTE_KEY_OFFSET + side - 1, now),
        )

    def both_held_ms(self):
        """How long both sides' buttons have been down together, or 0."""
        return min(self.held_ms(1), self.held_ms(2))

    @property
    def has_remotes(self):
        return self._remotes is not None

    def battery(self, side):
        """The side's remote battery charge in percent, or None if unknown."""
        return None if self._remotes is None else self._remotes.battery(side)

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

def select_players(display, buttons, stats, start_names=None):
    """Tap for the next name, double tap for the previous one, hold to lock in (or unlock).

    The left button picks player 1, who starts at the left end. Names are
    listed most recently played first, and the cursors start on start_names
    (the last match's players, by the ends they finished at). Resting on a
    name shows that player's stats under it.

    Holding on STATS browses the stats, and the stats also cycle by
    themselves after IDLE_STATS_MS untouched. Either way the selection is
    kept. Returns the two selected names as listed (guests not yet numbered).
    """
    selection = NameSelection(
        stats.by_recent(PLAYER_NAMES) + (GUEST_NAME, STATS_ENTRY),
        shared_names=(GUEST_NAME,),
        menu_names=(STATS_ENTRY,),
        start_names=start_names,
    )
    screen = None
    while not selection.complete:
        now = supervisor.ticks_ms()
        if screen is None:
            screen = NameSelectDisplay(
                display, menu_names=(STATS_ENTRY,), show_batteries=buttons.has_remotes
            )
            buttons.clear(double_tap=True)
            idle_since = now
            # Per player: the name the cursor is on and when it got there.
            resting = [(None, now), (None, now)]
            shown = None
            # Worked out once: ranking every player on each pass would be slow.
            name_stats = {
                name: summary(stats.record(name), stats.rank(name), HALF_CHARS)
                for name in PLAYER_NAMES
            }
        event = buttons.next_gesture()
        if event is not None:
            idle_since = now
            player, gesture = event
            if gesture == TAP:
                selection.cycle(player)
            elif gesture == DOUBLE_TAP:
                selection.cycle_back(player)
            elif selection.on_menu(player):
                show_stats(display, buttons, stats, stats_pages(display, stats), browse=True)
                screen = None
                continue
            else:
                selection.toggle_lock(player)
        elif stats.has_stats and ticks_diff(now, idle_since) >= IDLE_STATS_MS:
            show_stats(display, buttons, stats, stats_pages(display, stats), repeat=True)
            screen = None
            continue
        summaries = []
        for index in range(2):
            name = selection.current(index + 1)
            if resting[index][0] != name:
                resting[index] = (name, now)
            rested = ticks_diff(now, resting[index][1]) >= NAME_STATS_DELAY_MS
            summaries.append(name_stats.get(name) if rested else None)
        batteries = (buttons.battery(1), buttons.battery(2))
        state = (selection.current(1), selection.current(2),
                 selection.is_locked(1), selection.is_locked(2), summaries[0], summaries[1],
                 batteries)
        if state != shown:
            screen.render(selection, summaries, batteries)
            shown = state
        time.sleep(LOOP_DELAY_S)
    time.sleep(READY_PAUSE_S)
    return selection.selected_names

def select_server(display, buttons, player_names, best_of):
    """Tap your button to serve first, then hold either button to start.

    A double tap on either button switches to the next of BEST_OF_CHOICES.
    Returns the player who serves first and the chosen best of.
    """
    screen = ServeSelectDisplay(display, player_names)
    server = None
    screen.render(server, best_of)
    buttons.clear(double_tap=True)
    while True:
        event = buttons.next_gesture()
        if event is not None:
            side, gesture = event
            if gesture == HOLD:
                if server is not None:
                    return server, best_of
            elif gesture == DOUBLE_TAP:
                index = BEST_OF_CHOICES.index(best_of)
                best_of = BEST_OF_CHOICES[(index + 1) % len(BEST_OF_CHOICES)]
                screen.render(server, best_of)
            else:
                # Player 1 starts on the left, so the side is the player.
                server = side
                screen.render(server, best_of)
        time.sleep(LOOP_DELAY_S)

def play_match(display, buttons, player_names, match):
    """Play until the match has a winner.

    A press awards a point to the player at that end of the table, and a
    double tap on either button undoes the last point. Players change ends
    between games by themselves, but the switch in the middle of the deciding
    game is easy to forget, so the board asks for it before showing the
    swapped scoreboard.
    """
    scoreboard = ScoreboardDisplay(display, player_names)
    scoreboard.render(match)
    buttons.clear(double_tap=True)
    # The player who should be standing at the left end.
    shown_left = match.left_player
    while match.winner is None:
        event = buttons.next_gesture()
        if event is not None:
            side, gesture = event
            games = match.games
            if gesture == DOUBLE_TAP:
                if match.can_undo:
                    match.undo_last_point()
            else:
                match.award_point(match.player_on_side(side))
            if match.games != games:
                # A switch between games (or an undo back across one) needs no message.
                shown_left = match.left_player
            # The winning point needs no switch: the winner screen comes next.
            # An undo on the message can make another switch necessary, so check again.
            while match.winner is None and match.left_player != shown_left:
                games = match.games
                if announce_switch(display, buttons, match) or match.games != games:
                    shown_left = match.left_player
                scoreboard.show()
                buttons.clear(double_tap=True)
            scoreboard.render(match)
        time.sleep(LOOP_DELAY_S)

def announce_switch(display, buttons, match):
    """Ask the players to change ends until either button is tapped.

    Returns True once a tap confirms it. A double tap undoes the last point
    instead (such as a point awarded by mistake) and returns False.
    Holds, and double taps with nothing to undo, are ignored.
    """
    MessageDisplay(display, ("SWITCH", "SIDES"), hint="TAP=OK  2TAP=UNDO", color=WINNER_COLOR)
    # A press already under way when the message appears doesn't dismiss it.
    buttons.clear(double_tap=True)
    while True:
        event = buttons.next_gesture()
        if event is not None:
            _, gesture = event
            if gesture == TAP:
                return True
            if gesture == DOUBLE_TAP and match.can_undo:
                match.undo_last_point()
                return False
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

def player_card_page(display, stats, name):
    """A (duration, show) page for the player's card."""
    return CARD_PAGE_MS, lambda: PlayerCardDisplay(display, name, stats.record(name), stats.rank(name))

def stats_pages(display, stats):
    """(duration, show) pages: the leaderboard, then each ranked player's card."""
    ranking = stats.ranking()
    if not ranking:
        return [(CARD_PAGE_MS, lambda: MessageDisplay(display, ("NO STATS", "YET")))]
    pages = []
    for start in range(0, len(ranking), LEADERBOARD_ROWS):
        entries = ranking[start:start + LEADERBOARD_ROWS]
        pages.append((
            LEADERBOARD_PAGE_MS,
            lambda entries=entries, start=start: LeaderboardDisplay(display, entries, start + 1),
        ))
    for name, _ in ranking:
        pages.append(player_card_page(display, stats, name))
    return pages

def show_stats(display, buttons, stats, pages, browse=False, repeat=False):
    """Show stats pages until the viewer leaves.

    Browsing: tap for the next page, double tap for the previous one, hold to
    leave; also leaves after STATS_BROWSE_TIMEOUT_MS untouched. Otherwise each
    page shows for its own duration and any press leaves; repeat loops the
    pages instead of leaving after the last one.

    Holding both buttons for RESET_HOLD_MS asks whether to reset all stats.
    """
    index = 0
    pages[index][1]()
    buttons.clear(double_tap=browse)
    shown_at = supervisor.ticks_ms()
    while True:
        event = buttons.next_gesture()
        if buttons.both_held_ms() >= RESET_HOLD_MS:
            confirm_reset(display, buttons, stats)
            return
        if event is not None:
            side, gesture = event
            # A hold while the other button is down may be the start of a reset.
            if not (gesture == HOLD and buttons.held_ms(3 - side)):
                if not browse or gesture == HOLD:
                    return
                index = (index + (1 if gesture == TAP else -1)) % len(pages)
                pages[index][1]()
                shown_at = supervisor.ticks_ms()
        elapsed = ticks_diff(supervisor.ticks_ms(), shown_at)
        if browse:
            if elapsed >= STATS_BROWSE_TIMEOUT_MS:
                return
        elif elapsed >= pages[index][0]:
            index += 1
            if index == len(pages):
                if not repeat:
                    return
                index = 0
            pages[index][1]()
            shown_at = supervisor.ticks_ms()
        time.sleep(LOOP_DELAY_S)

def confirm_reset(display, buttons, stats):
    """Reset all stats if both buttons are held again; any other press cancels."""
    MessageDisplay(display, ("RESET ALL", "STATS?"), hint="HOLD BOTH=YES TAP=NO", color=WINNER_COLOR)
    # The buttons still down from the request must be released and pressed again.
    buttons.clear()
    shown_at = supervisor.ticks_ms()
    while ticks_diff(supervisor.ticks_ms(), shown_at) < RESET_CONFIRM_TIMEOUT_MS:
        event = buttons.next_gesture()
        if buttons.both_held_ms() >= RESET_CONFIRM_HOLD_MS:
            stats.reset()
            MessageDisplay(display, ("STATS", "RESET"))
            time.sleep(READY_PAUSE_S)
            break
        if event is not None:
            side, gesture = event
            if not (gesture == HOLD and buttons.held_ms(3 - side)):
                break
        time.sleep(LOOP_DELAY_S)
    buttons.clear()

def show_match_stats(display, buttons, stats, player_names, winner):
    """Briefly show the winner's and then the loser's updated card (guests have none)."""
    order = (player_names[winner - 1], player_names[2 - winner])
    pages = [player_card_page(display, stats, name) for name in order if stats.record(name)]
    if pages:
        show_stats(display, buttons, stats, pages)

def crash_report(error, uptime_s):
    """The text saved in the crash log: how long the board had run, and the traceback."""
    try:
        import traceback
        details = "".join(traceback.format_exception(error))
    except ImportError:
        details = repr(error)
    return "Crashed after {} min\n{}".format(int(uptime_s // 60), details)

def run(display, stats):
    remotes = RemoteReceiver(REMOTE_TIMEOUT_MS) if REMOTES_ENABLED else None
    buttons = ButtonInput(hold_ms=HOLD_MS, double_tap_ms=DOUBLE_TAP_MS, remotes=remotes)
    start_names = None
    best_of = DEFAULT_BEST_OF
    try:
        while True:
            selected = select_players(display, buttons, stats, start_names)
            player_names = distinct_names(selected)
            first_server, best_of = select_server(display, buttons, player_names, best_of)
            match = TableTennisMatch(first_server=first_server, games_to_win=games_to_win(best_of))
            while True:
                play_match(display, buttons, player_names, match)
                if not announce_winner(display, buttons, player_names, match):
                    break
            stats.record_match(player_names, match.games, match.winner)
            # Start the next name selection with each player at the end they finished at.
            left = match.left_player
            start_names = (selected[left - 1], selected[2 - left])
            show_match_stats(display, buttons, stats, player_names, match.winner)
    finally:
        buttons.deinit()

def main():
    """Run the scoreboard, saving a report of any crash and then restarting.

    A crash within CRASH_RESTART_MIN_UPTIME_S of starting is saved but stops
    the board as before (red status light), so a crash on every start doesn't
    restart it over and over.
    """
    started = time.monotonic()
    nvm = microcontroller.nvm
    crash_log = CrashLog(nvm)
    saved = crash_log.load()
    if saved is not None:
        print("Last crash (saved in non-volatile memory):\n" + saved)
    display = None
    try:
        validate_player_names(
            PLAYER_NAMES + (GUEST_NAME, STATS_ENTRY) + distinct_names((GUEST_NAME, GUEST_NAME))
        )
        stats = StatsBook(PLAYER_NAMES, NvmStore(nvm, size=len(nvm) - CRASH_LOG_SIZE))
        matrix = Matrix(width=WIDTH, height=HEIGHT, bit_depth=2, color_order=MATRIX_COLOR_ORDER)
        display = matrix.display
        run(display, stats)
    except Exception as error:
        uptime = time.monotonic() - started
        try:
            crash_log.save(crash_report(error, uptime))
        except Exception as log_error:
            print("Could not save the crash report:", repr(log_error))
        if uptime < CRASH_RESTART_MIN_UPTIME_S:
            raise
        try:
            MessageDisplay(display, ("ERROR",), hint="RESTARTING", color=ERROR_COLOR)
        except Exception:
            pass  # The display may be what failed.
        time.sleep(CRASH_MESSAGE_S)
        microcontroller.reset()
