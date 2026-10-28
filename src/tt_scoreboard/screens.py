import displayio
import terminalio
import vectorio
from adafruit_display_text import label

P1_COLOR = 0x00A0FF
P2_COLOR = 0x00A0FF
SCORE_COLOR = 0xFFFFFF
LINE_COLOR = 0x202040
SERVE_COLOR = 0xFFD000
GAME_COLOR = 0x00C000
LOCKED_COLOR = 0x00C000
HINT_COLOR = 0x606060
WINNER_COLOR = 0xFFD000
# Menu entries in the name list (such as STATS), so they don't read as names.
MENU_COLOR = 0xC000FF
# Remote battery charge: at least BATTERY_OK_PERCENT is green, at least
# BATTERY_LOW_PERCENT yellow, and below that red.
BATTERY_OK_COLOR = 0x00C000
BATTERY_LOW_COLOR = 0xFFD000
BATTERY_EMPTY_COLOR = 0xFF0000
BATTERY_OK_PERCENT = 50
BATTERY_LOW_PERCENT = 20
# The remotes' button colors, left end of the table first.
REMOTE_NAMES = ("BLUE", "RED")
REMOTE_COLORS = (0x0040FF, 0xFF0000)

WIDTH = 128
HEIGHT = 64
HALF = WIDTH // 2
NAME_MARGIN = 2
SERVE_BAR_WIDTH = 2
SERVE_BAR_GAP = 1
# terminalio.FONT glyphs are 6 pixels wide at scale 1.
GLYPH_WIDTH = 6

# Characters that fit across half the board, inside the margins.
HALF_CHARS = (HALF - 2 * NAME_MARGIN) // GLYPH_WIDTH

LEADERBOARD_ROWS = 4
# Leaderboard columns: rank and record/rate are right-aligned at these x
# positions, names left-aligned. Fits a 9-letter name, "12-10" and "100%".
RANK_RIGHT = 6
NAME_LEFT = 9
RECORD_RIGHT = 97
RATE_RIGHT = WIDTH - 1

def solid(color):
    palette = displayio.Palette(1)
    palette[0] = color
    return palette

def rect(x, y, w, h, color):
    return vectorio.Rectangle(pixel_shader=solid(color), x=x, y=y, width=w, height=h)

def text(txt, color, x, y, scale=1, anchor_x=0.5):
    """A label anchored at (x, y): centered by default, anchor_x 0 for left and 1 for right."""
    return label.Label(
        terminalio.FONT,
        text=txt,
        color=color,
        scale=scale,
        anchor_point=(anchor_x, 0.5),
        anchored_position=(x,y)
    )

def fit_scale(txt, width, max_scale):
    """Largest scale (at least 1) at which txt fits within width pixels."""
    return max(1, min(max_scale, width // (GLYPH_WIDTH * len(txt))))

def player_color(index):
    return P1_COLOR if index == 0 else P2_COLOR

def battery_charge(percent):
    """Text and charge tier color for a remote's battery (percent may be None)."""
    if percent is None:
        return "--", HINT_COLOR
    if percent >= BATTERY_OK_PERCENT:
        color = BATTERY_OK_COLOR
    elif percent >= BATTERY_LOW_PERCENT:
        color = BATTERY_LOW_COLOR
    else:
        color = BATTERY_EMPTY_COLOR
    return "{}%".format(percent), color

def section_center(index):
    return HALF // 2 + index * HALF

def split_layout():
    """Background shared by the two-column screens: header, body, and footer rows."""
    root = displayio.Group()
    root.append(rect(HALF-1, 0,2,HEIGHT,LINE_COLOR))
    root.append(rect(0,11,WIDTH,1,LINE_COLOR))
    root.append(rect(0,51,WIDTH,1,LINE_COLOR))
    return root

def _name_header(name, side, player):
    """Build the scoreboard name label and the x positions of its serve bars.

    side and player are 0-based indexes: side picks the half of the board, and
    player the name's color.
    """
    if not isinstance(name, str) or not name.strip() or "\n" in name or "\r" in name:
        raise ValueError("Player {} name must be nonempty single-line text".format(player + 1))
    name_label = text(name, player_color(player), section_center(side), 5)
    bounds = name_label.bounding_box
    name_width = bounds[2]
    name_left = name_label.x + bounds[0]
    left_bar = name_left - SERVE_BAR_GAP - SERVE_BAR_WIDTH
    right_bar = name_left + name_width + SERVE_BAR_GAP
    section_left = side * HALF
    if(
        left_bar < section_left + NAME_MARGIN
        or right_bar + SERVE_BAR_WIDTH > section_left + HALF - NAME_MARGIN
    ):
        raise ValueError("Player name is too wide: {}".format(name))
    return name_label, left_bar, right_bar

def validate_player_names(names):
    """Raise ValueError if any name cannot be shown on the scoreboard."""
    for name in names:
        _name_header(name, 0, 0)

class ScoreboardDisplay:
    """Shows each player on the half of the board matching their end of the table."""

    def __init__(self, display, player_names):
        if len(player_names) != 2:
            raise ValueError("Exactly two player names are required")

        root = split_layout()

        self._scores = []
        self._games = []
        # Per side, a (header, serve markers) pair for each player, since either
        # player may stand on either side. Only the current one is shown.
        self._headers = []
        for side in range(2):
            center = section_center(side)
            headers = []
            for player, name in enumerate(player_names):
                name_label, left_bar, right_bar = _name_header(name, side, player)
                header = displayio.Group()
                header.append(name_label)
                markers = displayio.Group()
                markers.append(rect(left_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
                markers.append(rect(right_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
                header.append(markers)
                header.hidden = True
                headers.append((header, markers))
                root.append(header)
            self._headers.append(headers)

            score = text("0", SCORE_COLOR, center, 31, scale=3)
            games = text("GAMES 0", GAME_COLOR, center, 57)
            self._scores.append(score)
            self._games.append(games)
            root.append(score)
            root.append(games)

        display.root_group = root

    def render(self, match):
        for side in range(2):
            player = match.player_on_side(side + 1)
            for index, (header, markers) in enumerate(self._headers[side]):
                header.hidden = index + 1 != player
                markers.hidden = player != match.server
            score_text = str(match.points[player - 1])
            self._scores[side].scale = max(1, min(3, 9 // len(score_text)))
            self._scores[side].text = score_text
            self._games[side].text = "GAMES {}".format(match.games[player - 1])

class NameSelectDisplay:
    """Picks the two players. With show_batteries, each half's header shows
    that end's remote (by button color) and its battery charge, such as
    BLUE 87%, in place of PLAYER 1 or PLAYER 2.
    """

    def __init__(self, display, menu_names=(), show_batteries=False):
        self._menu_names = menu_names
        self._show_batteries = show_batteries
        root = split_layout()
        # Per side, the remote's name and its charge, as separate labels so
        # each has its own color.
        self._remote_labels = []
        self._charges = []
        self._names = []
        self._statuses = []
        for index in range(2):
            center = section_center(index)
            if show_batteries:
                remote = text(REMOTE_NAMES[index], REMOTE_COLORS[index], center, 5, anchor_x=0)
                charge = text(" ", HINT_COLOR, center, 5, anchor_x=0)
                self._remote_labels.append(remote)
                self._charges.append(charge)
                root.append(remote)
                root.append(charge)
            else:
                root.append(text("PLAYER {}".format(index + 1), player_color(index), center, 5))
            # Fixed scale so every name is drawn with the same stroke width.
            name = text(" ", SCORE_COLOR, center, 31)
            status = text(" ", HINT_COLOR, center, 57)
            self._names.append(name)
            self._statuses.append(status)
            root.append(name)
            root.append(status)
        display.root_group = root

    def render(self, selection, summaries=(None, None), batteries=(None, None)):
        """summaries: per player, a stats line to show in place of HOLD=LOCK, or None.

        batteries: per side, the remote's charge in percent, or None if unknown.
        """
        for index in range(2):
            if self._show_batteries:
                self._render_battery(index, batteries[index])
            player = index + 1
            name = selection.current(player)
            locked = selection.is_locked(player)
            name_label = self._names[index]
            name_label.text = name
            status = self._statuses[index]
            if name in self._menu_names:
                name_label.color = MENU_COLOR
                status.text = "HOLD=OPEN"
                status.color = HINT_COLOR
            elif locked:
                name_label.color = LOCKED_COLOR
                status.text = "READY"
                status.color = LOCKED_COLOR
            elif summaries[index] is not None:
                name_label.color = SCORE_COLOR
                status.text = summaries[index]
                status.color = P1_COLOR
            else:
                name_label.color = SCORE_COLOR
                status.text = "HOLD=LOCK"
                status.color = HINT_COLOR

    def _render_battery(self, side, percent):
        """Center the side's "NAME CHARGE" header, whose width changes with the charge."""
        charge_text, color = battery_charge(percent)
        remote_text = REMOTE_NAMES[side]
        width = (len(remote_text) + 1 + len(charge_text)) * GLYPH_WIDTH
        left = section_center(side) - width // 2
        charge = self._charges[side]
        charge.text = charge_text
        charge.color = color
        charge.anchored_position = (left + (len(remote_text) + 1) * GLYPH_WIDTH, 5)
        self._remote_labels[side].anchored_position = (left, 5)

class ServeSelectDisplay:
    """Asks who serves first, with serve bars around the chosen player's name.

    Player 1 is on the left, as at the start of the match.
    """

    def __init__(self, display, player_names):
        if len(player_names) != 2:
            raise ValueError("Exactly two player names are required")
        root = split_layout()
        self._markers = []
        self._serve_labels = []
        self._hints = []
        for index, name in enumerate(player_names):
            center = section_center(index)
            name_label, left_bar, right_bar = _name_header(name, index, index)
            root.append(name_label)
            markers = displayio.Group()
            markers.append(rect(left_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
            markers.append(rect(right_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
            self._markers.append(markers)
            root.append(markers)
            serve_label = text("SERVE", SERVE_COLOR, center, 31, scale=2)
            hint = text(" ", HINT_COLOR, center, 57)
            self._serve_labels.append(serve_label)
            self._hints.append(hint)
            root.append(serve_label)
            root.append(hint)
        display.root_group = root

    def render(self, server):
        """server is the chosen player (1 or 2), or None before anyone is chosen."""
        for index in range(2):
            chosen = index + 1 == server
            self._markers[index].hidden = not chosen
            self._serve_labels[index].hidden = not chosen
            self._hints[index].text = "TAP=SERVE" if server is None else "HOLD=START"

class WinnerDisplay:

    def __init__(self, display, winner_name, winner_games, loser_games):
        root = displayio.Group()
        root.append(text("WINNER", WINNER_COLOR, HALF, 9, scale=2))
        name_scale = fit_scale(winner_name, WIDTH - 2 * NAME_MARGIN, 3)
        root.append(text(winner_name, SCORE_COLOR, HALF, 33, scale=name_scale))
        score = "{} - {}".format(winner_games, loser_games)
        root.append(text(score, GAME_COLOR, HALF, 56))
        display.root_group = root

def format_record(won, lost):
    return "{}-{}".format(won, lost)

def format_rate(rate):
    return "--" if rate is None else "{}%".format(rate)

class LeaderboardDisplay:
    """One page of the leaderboard: rank, name, match record and match win rate."""

    def __init__(self, display, entries, first_rank):
        root = displayio.Group()
        root.append(rect(0, 11, WIDTH, 1, LINE_COLOR))
        root.append(text("PLAYER", HINT_COLOR, NAME_LEFT, 5, anchor_x=0))
        root.append(text("W-L", HINT_COLOR, RECORD_RIGHT, 5, anchor_x=1))
        root.append(text("WIN", HINT_COLOR, RATE_RIGHT, 5, anchor_x=1))
        for row, (name, record) in enumerate(entries):
            y = 18 + row * 12
            root.append(text(str(first_rank + row), HINT_COLOR, RANK_RIGHT, y, anchor_x=1))
            root.append(text(name, SCORE_COLOR, NAME_LEFT, y, anchor_x=0))
            record_text = format_record(record.matches_won, record.matches_lost)
            root.append(text(record_text, SCORE_COLOR, RECORD_RIGHT, y, anchor_x=1))
            rate_text = format_rate(record.match_win_rate)
            root.append(text(rate_text, GAME_COLOR, RATE_RIGHT, y, anchor_x=1))
        display.root_group = root

class PlayerCardDisplay:
    """One player's stats: matches on the left, games on the right."""

    def __init__(self, display, name, record, rank):
        root = displayio.Group()
        root.append(rect(0, 11, WIDTH, 1, LINE_COLOR))
        root.append(rect(0, 51, WIDTH, 1, LINE_COLOR))
        root.append(rect(HALF - 1, 12, 2, 39, LINE_COLOR))
        root.append(text(name, P1_COLOR, HALF, 5))
        columns = (
            ("MATCHES", record.matches_won, record.matches_lost, record.match_win_rate),
            ("GAMES", record.games_won, record.games_lost, record.game_win_rate),
        )
        for index, (heading, won, lost, rate) in enumerate(columns):
            center = section_center(index)
            root.append(text(heading, HINT_COLOR, center, 17))
            root.append(text(format_record(won, lost), SCORE_COLOR, center, 28))
            root.append(text(format_rate(rate), GAME_COLOR, center, 42, scale=2))
        played = "{} PLAYED".format(record.matches_played)
        footer = played if rank is None else "RANK {}  {}".format(rank, played)
        root.append(text(footer, HINT_COLOR, HALF, 57))
        display.root_group = root

class MessageDisplay:
    """One or two lines of large text, with an optional hint along the bottom."""

    def __init__(self, display, lines, hint=None, color=SCORE_COLOR):
        root = displayio.Group()
        rows = (28,) if len(lines) == 1 else (18, 38)
        for line, y in zip(lines, rows):
            root.append(text(line, color, HALF, y, scale=fit_scale(line, WIDTH - 2 * NAME_MARGIN, 2)))
        if hint is not None:
            root.append(text(hint, HINT_COLOR, HALF, 57))
        display.root_group = root
