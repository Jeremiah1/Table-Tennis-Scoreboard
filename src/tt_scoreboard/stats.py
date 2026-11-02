"""Per-player match statistics, saved in the board's non-volatile memory.

Four counts are stored per player, plus the number of the last match they
played; everything shown is derived from them. Stats are keyed by name, so
editing the player list keeps them: a removed player is hidden but kept, and
comes back if the name is added again.
"""
import json

# Blob layout: magic, version, payload length (2 bytes), JSON payload.
_MAGIC = b"TS"
_VERSION = 1
_HEADER_SIZE = 5

# The leaderboard ranks by win rate as if every player had these extra
# matches, half of them won, so a lucky start can't hold first place.
PRIOR_MATCHES = 4
PRIOR_WINS = 2
# Players who haven't played in this many recorded matches are inactive:
# hidden from the leaderboard until they play again.
ACTIVE_MATCHES = 30


def percent(won, played):
    """Whole-number percentage, or None when nothing has been played."""
    if played == 0:
        return None
    return int(100 * won / played + 0.5)


def summary(record, rank, max_chars):
    """A short line such as "#3 8-4 67%", dropping parts until it fits in max_chars.

    rank is the leaderboard position, or None for a player who isn't on it.
    Returns None for a player with no matches.
    """
    if record is None or record.matches_played == 0:
        return None
    win_rate = "{}%".format(record.match_win_rate)
    played = "{}-{}".format(record.matches_won, record.matches_lost)
    ranked = "#{}".format(rank) if rank is not None else None
    candidates = (
        (ranked, played, win_rate),
        (played, win_rate),
        (ranked, win_rate),
        (win_rate,),
    )
    for parts in candidates:
        line = " ".join(part for part in parts if part is not None)
        if len(line) <= max_chars:
            return line
    return win_rate

class PlayerRecord:

    def __init__(self, counts):
        self.matches_won, self.matches_lost, self.games_won, self.games_lost = counts[:4]
        # Number of the last match played (matches are numbered from 1), or 0.
        self.last_match = counts[4] if len(counts) > 4 else 0

    @property
    def matches_played(self):
        return self.matches_won + self.matches_lost

    @property
    def match_win_rate(self):
        return percent(self.matches_won, self.matches_played)

    @property
    def game_win_rate(self):
        return percent(self.games_won, self.games_won + self.games_lost)

    @property
    def ranking_score(self):
        return (self.matches_won + PRIOR_WINS) / (self.matches_played + PRIOR_MATCHES)


class NvmStore:
    """Saves one blob at the start of a bytearray-like memory (microcontroller.nvm).

    The end of microcontroller.nvm holds the crash log, so the scoreboard
    passes a size that stops short of it.
    """

    def __init__(self, memory, size=None):
        """size limits the blob to the first size bytes, leaving the rest for other uses."""
        self._memory = memory
        self._size = len(memory) if size is None else size

    def load(self):
        """Return the saved payload, or None if there is none or it is damaged."""
        header = bytes(self._memory[0:_HEADER_SIZE])
        if header[0:2] != _MAGIC or header[2] != _VERSION:
            return None
        length = int.from_bytes(header[3:5], "big")
        if _HEADER_SIZE + length > self._size:
            return None
        return bytes(self._memory[_HEADER_SIZE:_HEADER_SIZE + length])

    def save(self, payload):
        blob = _MAGIC + bytes((_VERSION,)) + len(payload).to_bytes(2, "big") + payload
        if len(blob) > self._size:
            raise ValueError("Stats do not fit in non-volatile memory")
        self._memory[0:len(blob)] = blob


class StatsBook:
    """Win/loss counts for the tracked players (guests are not tracked)."""

    def __init__(self, tracked_names, store=None, active_matches=ACTIVE_MATCHES):
        self._tracked = tuple(tracked_names)
        self._store = store
        self._active_matches = active_matches
        # Matches recorded so far; also the number of the latest match.
        self._match_count = 0
        # name -> [matches won, matches lost, games won, games lost, last match]
        self._counts = {}
        if store is not None:
            self._load(store.load())

    def _load(self, payload):
        if payload is None:
            return
        try:
            data = json.loads(payload.decode())
            if "players" in data:
                match_count, players = int(data["matches"]), data["players"]
            else:
                # Before match numbers were kept: only the four counts per player.
                match_count, players = 0, data
            counts = {}
            for name, values in players.items():
                values = [int(value) for value in values]
                if len(values) == 4:
                    values.append(0)
                if len(values) == 5:
                    counts[name] = values
        except (ValueError, AttributeError, TypeError, KeyError):
            print("Saved stats are damaged; starting fresh")
            return
        self._match_count = match_count
        self._counts = counts

    def _save(self):
        if self._store is not None:
            data = {"matches": self._match_count, "players": self._counts}
            self._store.save(json.dumps(data).encode())

    def record_match(self, player_names, games, winner):
        """Count a finished match. Names that are not tracked are skipped."""
        tracked = [name in self._tracked for name in player_names]
        if not any(tracked):
            return
        self._match_count += 1
        for index, name in enumerate(player_names):
            if not tracked[index]:
                continue
            counts = self._counts.setdefault(name, [0, 0, 0, 0, 0])
            counts[0 if index + 1 == winner else 1] += 1
            counts[2] += games[index]
            counts[3] += games[1 - index]
            counts[4] = self._match_count
        self._save()

    def record(self, name):
        """The player's record, or None for an untracked name."""
        if name not in self._tracked:
            return None
        return PlayerRecord(self._counts.get(name, (0, 0, 0, 0, 0)))

    def is_active(self, name):
        """Whether the player has played within the last active_matches matches."""
        record = self.record(name)
        return (
            record is not None
            and record.matches_played > 0
            and self._match_count - record.last_match < self._active_matches
        )

    def by_recent(self, names):
        """names reordered most recently played first.

        Names that have never played (or are not tracked) keep their order, after the others.
        """
        played = []
        unplayed = []
        for order, name in enumerate(names):
            record = self.record(name)
            if record is not None and record.last_match:
                played.append((-record.last_match, order, name))
            else:
                unplayed.append(name)
        played.sort()
        return tuple(name for _, _, name in played) + tuple(unplayed)

    def ranking(self):
        """(name, record) pairs for active players, best first.

        Ties on ranking score go to the better game win rate, then to more
        matches played, then to the order of the player list.
        """
        ranked = []
        for order, name in enumerate(self._tracked):
            if self.is_active(name):
                ranked.append((name, self.record(name), order))
        ranked.sort(key=lambda entry: (
            -entry[1].ranking_score,
            -(entry[1].game_win_rate or 0),
            -entry[1].matches_played,
            entry[2],
        ))
        return [(name, record) for name, record, _ in ranked]

    def rank(self, name):
        """The player's leaderboard position (from 1), or None if unranked."""
        for position, (ranked_name, _) in enumerate(self.ranking()):
            if ranked_name == name:
                return position + 1
        return None

    @property
    def has_stats(self):
        """Whether anyone is on the leaderboard."""
        return any(self.is_active(name) for name in self._tracked)

    def reset(self):
        """Forget every player's stats, including players no longer tracked."""
        self._match_count = 0
        self._counts = {}
        self._save()
