class NameSelection:
    """Two players each browse a shared list of names and lock one in.

    A name locked by one player is skipped while the other player browses,
    unless it is one of shared_names (such as a guest name), which both
    players may lock in.

    menu_names are entries that open something instead of naming a player
    (such as STATS). Both players may browse to them, but they cannot be
    locked in.

    start_names, if given, are the names the two cursors start on (such as
    the last match's players); otherwise they start on the first two names.
    """

    def __init__(self, names, shared_names=(), menu_names=(), start_names=None):
        names = tuple(names)
        if len(names) < 2:
            raise ValueError("At least two names are required")
        if len(set(names)) != len(names):
            raise ValueError("Names must be unique")
        for name in shared_names + menu_names:
            if name not in names:
                raise ValueError("Name {} is not in the names list".format(name))
        if len(names) - len(menu_names) < 2:
            raise ValueError("At least two player names are required")
        self._names = names
        self._menu = tuple(names.index(name) for name in menu_names)
        self._shared = tuple(names.index(name) for name in shared_names) + self._menu
        self._cursors = [0, 1]
        self._locked = [False, False]
        if start_names is not None:
            cursors = [names.index(name) if name in names else -1 for name in start_names]
            if -1 not in cursors and (cursors[0] != cursors[1] or cursors[0] in self._shared):
                self._cursors = cursors

    @staticmethod
    def _validate_player(player):
        if player not in (1, 2):
            raise ValueError("Player must be 1 or 2")

    def current(self, player):
        self._validate_player(player)
        return self._names[self._cursors[player - 1]]

    def on_menu(self, player):
        """Whether the player's cursor is on a menu entry."""
        self._validate_player(player)
        return self._cursors[player - 1] in self._menu

    def is_locked(self, player):
        self._validate_player(player)
        return self._locked[player - 1]

    @property
    def complete(self):
        return all(self._locked)

    @property
    def selected_names(self):
        if not self.complete:
            raise ValueError("Both players must lock in a name first")
        return tuple(self._names[cursor] for cursor in self._cursors)

    def cycle(self, player):
        """Move the player's cursor to the next available name."""
        self._move(player, 1)

    def cycle_back(self, player):
        """Move the player's cursor to the previous available name."""
        self._move(player, -1)

    def _move(self, player, step):
        self._validate_player(player)
        if not self._locked[player - 1]:
            self._advance(player - 1, step)

    def toggle_lock(self, player):
        """Lock in the player's current name, or unlock it.

        Has no effect once both players have locked in, or on a menu entry.
        """
        self._validate_player(player)
        if self.complete or self.on_menu(player):
            return
        index = player - 1
        other = 1 - index
        self._locked[index] = not self._locked[index]
        if self._locked[index] and self._taken(other, self._cursors[other]):
            self._advance(other)

    def _taken(self, index, cursor):
        """Whether the name at cursor is locked in by the other player."""
        other = 1 - index
        return (
            self._locked[other]
            and cursor == self._cursors[other]
            and cursor not in self._shared
        )

    def _advance(self, index, step=1):
        cursor = self._cursors[index]
        while True:
            cursor = (cursor + step) % len(self._names)
            if not self._taken(index, cursor):
                break
        self._cursors[index] = cursor


def distinct_names(names):
    """Number the players' names if both picked the same (shared) name."""
    first, second = names
    if first == second:
        return "{} 1".format(first), "{} 2".format(second)
    return first, second

def parse_player_names(text, default=()):
    """Split a comma-separated list of names (as stored in settings.toml).

    Returns default if text is empty or missing.
    """
    names = tuple(name.strip() for name in str(text or "").split(",") if name.strip())
    if not names:
        return tuple(default)
    if len(set(names)) != len(names):
        raise ValueError("Player names must be unique")
    return names
