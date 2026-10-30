LEFT = 1
RIGHT = 2
# In the deciding game, players change ends when one of them reaches this score.
DECIDING_GAME_SWITCH_POINTS = 5

def games_to_win(best_of):
    """Games a player needs to win a best-of match: 3 for best of 5, 4 for best of 7."""
    if best_of < 1 or best_of % 2 == 0:
        raise ValueError("Best of must be a positive odd number")
    return best_of // 2 + 1

class TableTennisMatch:

    def __init__(self, first_server=1, games_to_win=4):
        self._validate_player(first_server)
        if games_to_win < 1:
            raise ValueError("Games to win must be at least 1")
        self._first_server = first_server
        self._games_to_win = games_to_win
        self._points = [0, 0]
        self._games = [0, 0]
        self._history = []

    @staticmethod
    def _validate_player(player):
        if player not in (1, 2):
            raise ValueError("Player must be 1 or 2")

    @property
    def points(self):
        return tuple(self._points)

    @property
    def games(self):
        return tuple(self._games)

    @property
    def winner(self):
        for index, games in enumerate(self._games):
            if games >= self._games_to_win:
                return index + 1
        return None

    @property
    def deuce(self):
        return min(self._points) >= 10

    @property
    def server(self):
        total = sum(self._points)
        turns = total - 20 if self.deuce else total // 2
        return self._first_server if turns % 2 == 0 else 3 - self._first_server

    @property
    def deciding_game(self):
        return self._games[0] == self._games[1] == self._games_to_win - 1

    @property
    def left_player(self):
        """The player at the left end of the table. Player 1 starts there.

        Players change ends after every game, and once more in the deciding
        game when one of them reaches DECIDING_GAME_SWITCH_POINTS. Once the
        match is over, this is where they stood for the final game.
        """
        switches = sum(self._games)
        if self.winner is not None:
            # No next game: undo the switch after the final one, which (if it
            # was the deciding game) included the mid-game switch.
            switches -= 1
            if min(self._games) == self._games_to_win - 1:
                switches += 1
        elif self.deciding_game and max(self._points) >= DECIDING_GAME_SWITCH_POINTS:
            switches += 1
        return 1 if switches % 2 == 0 else 2

    def player_on_side(self, side):
        """The player at the LEFT or RIGHT end of the table."""
        if side not in (LEFT, RIGHT):
            raise ValueError("Side must be LEFT or RIGHT")
        left = self.left_player
        return left if side == LEFT else 3 - left

    @property
    def can_undo(self):
        return bool(self._history)

    def award_point(self, player):
        self._validate_player(player)
        if self.winner is not None:
            raise ValueError("Match is already over")
        self._history.append((self.points, self.games, self._first_server))
        self._points[player - 1] += 1
        if max(self._points) >= 11 and abs(self._points[0] - self._points[1]) >= 2:
            self._games[player - 1] += 1
            self._points = [0, 0]
            self._first_server = 3 - self._first_server
            return player
        return None

    def undo_last_point(self):
        """Restore the state before the most recent point still on record.

        Can be repeated to step back through the whole match, including the
        point that won the match.
        """
        if not self._history:
            raise ValueError("No point available to undo")
        points, games, first_server = self._history.pop()
        self._points = list(points)
        self._games = list(games)
        self._first_server = first_server
