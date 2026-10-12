import board
import displayio
import keypad
import terminalio
import time
import vectorio
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from scoring import TableTennisMatch

PLAYER_1 = "Alex"
PLAYER_2 = "SAM"
FIRST_SERVER = 1

P1_COLOR = 0x00A0FF
P2_COLOR = 0x00A0FF
SCORE_COLOR = 0xFFFFFF
LINE_COLOR = 0x202040
SERVE_COLOR = 0xFFD000
GAME_COLOR = 0x00C000

WIDTH = 128
HEIGHT = 64
HALF = WIDTH // 2
NAME_MARGIN = 2
SERVE_BAR_WIDTH = 2
SERVE_BAR_GAP = 1

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

class ScoreboardDisplay:

    def __init__(self, display, player_names):
        if len(player_names) != 2:
            raise ValueError("Exactly two player names are required")
        
        root = displayio.Group()
        root.append(rect(HALF-1, 0,2,HEIGHT,LINE_COLOR))
        root.append(rect(0,11,WIDTH,1,LINE_COLOR))
        root.append(rect(0,51,WIDTH,1,LINE_COLOR))

        self._scores = []
        self._games = []
        self._serve_markers = []
        for index, name in enumerate(player_names):
            if not isinstance(name, str) or not name.strip() or "\n" in name or "\r" in name:
                raise ValueError("Player {} name must be nonempty single-line text".format(index + 1))
            center = HALF // 2 + index * HALF
            color = P1_COLOR if index == 0 else P2_COLOR
            name_label = text(name, color, center, 5)
            bounds = name_label.bounding_box
            name_width = bounds[2]
            name_left = name_label.x + bounds[0]
            left_bar = name_left - SERVE_BAR_GAP - SERVE_BAR_WIDTH
            right_bar = name_left + name_width + SERVE_BAR_GAP
            section_left = index * HALF
            if(
                left_bar < section_left + NAME_MARGIN
                or right_bar + SERVE_BAR_WIDTH > section_left + HALF - NAME_MARGIN
            ):
                raise ValueError("Player name is too wide")

            root.append(name_label)
            markers = displayio.Group()
            markers.append(rect(left_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
            markers.append(rect(right_bar, 1, SERVE_BAR_WIDTH, 9, SERVE_COLOR))
            markers.hidden = True
            self._serve_markers.append(markers)
            root.append(markers)

            score = text("0", SCORE_COLOR, center, 31, scale=3)
            games = text("GAMES 0", GAME_COLOR, center, 57)
            self._scores.append(score)
            self._games.append(games)
            root.append(score)
            root.append(games)

        # self._serve = vectorio.Circle(
        #     pixel_shader=solid(SERVE_COLOR), radius=2, x=8, y=5
        # )
        # root.append(self._serve)
        display.root_group = root

    def render(self, match):
        for index, points in enumerate(match.points):
            score_text = str(points)
            self._scores[index].scale = max(1, min(3, 9 // len(score_text)))
            self._scores[index].text = score_text
            self._games[index].text = "GAMES {}".format(match.games[index])

        for index, markers in enumerate(self._serve_markers):
            markers.hidden = index + 1 != match.server

class ButtonInput:

    def __init__(self):
        self._keys = keypad.Keys(
            (board.BUTTON_UP, board.BUTTON_DOWN),
            value_when_pressed=False,
            pull=True,
            interval=0.03
        )

    def next_player(self):
        event = self._keys.events.get()
        while event is not None:
            if event.pressed:
                return event.key_number + 1
            event = self._keys.events.get()
        return None

    def deinit(self):
        self._keys.deinit()

def main():
    matrix = Matrix(width=WIDTH, height=HEIGHT, bit_depth=2)
    match = TableTennisMatch(first_server=FIRST_SERVER)
    scoreboard = ScoreboardDisplay(matrix.display, (PLAYER_1, PLAYER_2))
    buttons = ButtonInput()
    scoreboard.render(match)
    try:
        while True:
            player = buttons.next_player()
            if player is not None:
                match.award_point(player)
                scoreboard.render(match)
            time.sleep(0.01)
    finally:
        buttons.deinit()

if __name__ == "__main__":
    main()