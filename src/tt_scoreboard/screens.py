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

WIDTH = 128
HEIGHT = 64
HALF = WIDTH // 2
NAME_MARGIN = 2
SERVE_BAR_WIDTH = 2
SERVE_BAR_GAP = 1
# terminalio.FONT glyphs are 6 pixels wide at scale 1.
GLYPH_WIDTH = 6

def solid(color):
    palette = displayio.Palette(1)
    palette[0] = color
    return palette

def rect(x, y, w, h, color):
    return vectorio.Rectangle(pixel_shader=solid(color), x=x, y=y, width=w, height=h)

def text(txt, color, x, y, scale=1):
    return label.Label(
        terminalio.FONT,
        text=txt,
        color=color,
        scale=scale,
        anchor_point=(0.5, 0.5),
        anchored_position=(x,y)
    )

def fit_scale(txt, width, max_scale):
    """Largest scale (at least 1) at which txt fits within width pixels."""
    return max(1, min(max_scale, width // (GLYPH_WIDTH * len(txt))))

def player_color(index):
    return P1_COLOR if index == 0 else P2_COLOR

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

    def __init__(self, display):
        root = split_layout()
        self._names = []
        self._statuses = []
        for index in range(2):
            center = section_center(index)
            root.append(text("PLAYER {}".format(index + 1), player_color(index), center, 5))
            # Fixed scale so every name is drawn with the same stroke width.
            name = text(" ", SCORE_COLOR, center, 31)
            status = text(" ", HINT_COLOR, center, 57)
            self._names.append(name)
            self._statuses.append(status)
            root.append(name)
            root.append(status)
        display.root_group = root

    def render(self, selection):
        for index in range(2):
            player = index + 1
            name = selection.current(player)
            locked = selection.is_locked(player)
            name_label = self._names[index]
            name_label.text = name
            name_label.color = LOCKED_COLOR if locked else SCORE_COLOR
            status = self._statuses[index]
            status.text = "READY" if locked else "HOLD=LOCK"
            status.color = LOCKED_COLOR if locked else HINT_COLOR

class WinnerDisplay:

    def __init__(self, display, winner_name, winner_games, loser_games):
        root = displayio.Group()
        root.append(text("WINNER", WINNER_COLOR, HALF, 9, scale=2))
        name_scale = fit_scale(winner_name, WIDTH - 2 * NAME_MARGIN, 3)
        root.append(text(winner_name, SCORE_COLOR, HALF, 33, scale=name_scale))
        score = "{} - {}".format(winner_games, loser_games)
        root.append(text(score, GAME_COLOR, HALF, 56))
        display.root_group = root
