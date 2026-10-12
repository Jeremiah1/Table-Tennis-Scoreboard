class TableTennisMatch:

    def __init__(self, first_server=1):
        self._validate_player(first_server)
        self._first_server = first_server
        self._points = [0, 0]
        self._games = [0, 0]
        self._previous_state = None

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
    def deuce(self):
        return min(self._points) >= 10

    @property
    def server(self):
        total = sum(self._points)
        turns = total - 20 if self.deuce else total // 2
        return self._first_server if turns % 2 == 0 else 3 - self._first_server

    def award_point(self, player):
        self._validate_player(player)
        self._previous_state = (
            self.points, self.games, self._first_server
        )
        self._points[player - 1] += 1
        if max(self._points) >= 11 and abs(self._points[0] - self._points[1]) >= 2:
            self._games[player - 1] += 1
            self._points = [0, 0]
            self._first_server = 3 - self._first_server
            return player
        return None

    def undo_last_point(self):
        if self._previous_state is None:
            raise ValueError("No point available to undo")

        points, games, first_server = self._previous_state
        self._points  = list(points)
        self._games = list(games)
        self._first_server = first_server
        self._previous_state = None