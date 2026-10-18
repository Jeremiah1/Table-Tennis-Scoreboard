import unittest

from tt_scoreboard.stats import NvmStore, PlayerRecord, StatsBook, percent, summary

NAMES = ("ANN", "BOB", "CAL")


def book(store=None):
    return StatsBook(NAMES, store)


def play(stats, names, wins, games=None):
    """Record `wins` matches won by names[0] over names[1]."""
    for _ in range(wins):
        stats.record_match(names, games or (4, 1), 1)


class PlayerRecordTest(unittest.TestCase):

    def test_derived_stats(self):
        record = PlayerRecord((8, 4, 30, 18))
        self.assertEqual(record.matches_played, 12)
        self.assertEqual(record.match_win_rate, 67)
        self.assertEqual(record.game_win_rate, 63)

    def test_no_matches_has_no_rate(self):
        record = PlayerRecord((0, 0, 0, 0))
        self.assertIsNone(record.match_win_rate)
        self.assertIsNone(record.game_win_rate)

    def test_percent_rounds(self):
        self.assertEqual(percent(1, 3), 33)
        self.assertEqual(percent(2, 3), 67)
        self.assertEqual(percent(1, 1), 100)


class StatsBookTest(unittest.TestCase):

    def test_record_match_counts_both_players(self):
        stats = book()
        stats.record_match(("ANN", "BOB"), (4, 2), 1)
        ann, bob = stats.record("ANN"), stats.record("BOB")
        self.assertEqual((ann.matches_won, ann.matches_lost, ann.games_won, ann.games_lost), (1, 0, 4, 2))
        self.assertEqual((bob.matches_won, bob.matches_lost, bob.games_won, bob.games_lost), (0, 1, 2, 4))

    def test_untracked_names_are_skipped(self):
        stats = book()
        stats.record_match(("GUEST", "BOB"), (4, 0), 1)
        self.assertIsNone(stats.record("GUEST"))
        self.assertEqual(stats.record("BOB").matches_lost, 1)

    def test_ranking_hides_players_without_matches(self):
        stats = book()
        self.assertFalse(stats.has_stats)
        stats.record_match(("ANN", "BOB"), (4, 0), 1)
        self.assertTrue(stats.has_stats)
        self.assertEqual([name for name, _ in stats.ranking()], ["ANN", "BOB"])
        self.assertIsNone(stats.rank("CAL"))

    def test_one_lucky_win_does_not_top_a_strong_record(self):
        stats = book()
        stats.record_match(("CAL", "BOB"), (4, 0), 1)  # CAL 1-0
        play(stats, ("ANN", "BOB"), 8)  # ANN 8-4
        for _ in range(4):
            stats.record_match(("ANN", "BOB"), (1, 4), 2)
        self.assertEqual(stats.record("CAL").match_win_rate, 100)
        self.assertEqual(stats.rank("ANN"), 1)
        self.assertEqual(stats.rank("CAL"), 2)

    def test_ties_go_to_better_game_rate(self):
        stats = book()
        stats.record_match(("ANN", "CAL"), (4, 3), 1)
        stats.record_match(("BOB", "CAL"), (4, 0), 1)
        self.assertEqual([name for name, _ in stats.ranking()[:2]], ["BOB", "ANN"])

    def test_reset_clears_everything(self):
        stats = book()
        stats.record_match(("ANN", "BOB"), (4, 0), 1)
        stats.reset()
        self.assertFalse(stats.has_stats)


class PersistenceTest(unittest.TestCase):

    def setUp(self):
        self.memory = bytearray(256)

    def test_stats_survive_restart(self):
        book(NvmStore(self.memory)).record_match(("ANN", "BOB"), (4, 3), 2)
        reloaded = book(NvmStore(self.memory))
        self.assertEqual(reloaded.record("BOB").matches_won, 1)
        self.assertEqual(reloaded.record("ANN").games_won, 4)

    def test_blank_memory_starts_empty(self):
        self.assertFalse(book(NvmStore(self.memory)).has_stats)

    def test_damaged_payload_starts_empty(self):
        NvmStore(self.memory).save(b"{not json")
        self.assertFalse(book(NvmStore(self.memory)).has_stats)

    def test_removed_player_is_kept_and_returns(self):
        book(NvmStore(self.memory)).record_match(("ANN", "BOB"), (4, 0), 1)
        without_ann = StatsBook(("BOB", "CAL"), NvmStore(self.memory))
        self.assertIsNone(without_ann.record("ANN"))
        without_ann.record_match(("BOB", "CAL"), (4, 0), 1)
        self.assertEqual(book(NvmStore(self.memory)).record("ANN").matches_won, 1)

    def test_reset_is_saved(self):
        stats = book(NvmStore(self.memory))
        stats.record_match(("ANN", "BOB"), (4, 0), 1)
        stats.reset()
        self.assertFalse(book(NvmStore(self.memory)).has_stats)

    def test_too_big_for_memory_raises(self):
        with self.assertRaises(ValueError):
            NvmStore(bytearray(8)).save(b"0123456789")

    def test_full_roster_fits_in_nvm(self):
        names = tuple("PLAYER{:03}".format(i) for i in range(8))
        memory = bytearray(8192)
        stats = StatsBook(names, NvmStore(memory))
        for i in range(0, 8, 2):
            for _ in range(999):
                stats.record_match((names[i], names[i + 1]), (4, 3), 1)
        self.assertEqual(StatsBook(names, NvmStore(memory)).record(names[0]).matches_won, 999)


class SummaryTest(unittest.TestCase):

    def test_full_summary_when_it_fits(self):
        self.assertEqual(summary(PlayerRecord((8, 4, 0, 0)), 3, 10), "#3 8-4 67%")

    def test_drops_rank_then_record_to_fit(self):
        record = PlayerRecord((12, 10, 0, 0))
        self.assertEqual(summary(record, 12, 10), "12-10 55%")
        self.assertEqual(summary(record, 12, 7), "#12 55%")
        self.assertEqual(summary(record, 12, 4), "55%")

    def test_unranked_player_has_no_rank(self):
        self.assertEqual(summary(PlayerRecord((1, 0, 0, 0)), None, 10), "1-0 100%")

    def test_no_matches_has_no_summary(self):
        self.assertIsNone(summary(PlayerRecord((0, 0, 0, 0)), None, 10))
        self.assertIsNone(summary(None, None, 10))


class RecencyTest(unittest.TestCase):

    def test_by_recent_orders_latest_first_and_unplayed_last(self):
        stats = StatsBook(("ANN", "BOB", "CAL", "DAN"))
        stats.record_match(("BOB", "CAL"), (4, 0), 1)
        stats.record_match(("DAN", "BOB"), (4, 0), 1)
        self.assertEqual(stats.by_recent(("ANN", "BOB", "CAL", "DAN", "GUEST")),
                         ("BOB", "DAN", "CAL", "ANN", "GUEST"))

    def test_inactive_players_leave_the_leaderboard(self):
        stats = StatsBook(NAMES, active_matches=3)
        stats.record_match(("CAL", "BOB"), (4, 0), 1)
        for _ in range(2):
            stats.record_match(("ANN", "BOB"), (4, 0), 1)
        self.assertIn("CAL", [name for name, _ in stats.ranking()])
        stats.record_match(("ANN", "BOB"), (4, 0), 1)
        self.assertNotIn("CAL", [name for name, _ in stats.ranking()])
        self.assertIsNone(stats.rank("CAL"))
        self.assertEqual(stats.record("CAL").matches_won, 1)
        stats.record_match(("CAL", "BOB"), (4, 0), 1)
        self.assertIsNotNone(stats.rank("CAL"))

    def test_guest_only_match_is_not_numbered(self):
        stats = book()
        stats.record_match(("GUEST 1", "GUEST 2"), (4, 0), 1)
        stats.record_match(("ANN", "BOB"), (4, 0), 1)
        self.assertEqual(stats.record("ANN").last_match, 1)

    def test_old_saved_layout_is_migrated(self):
        memory = bytearray(256)
        NvmStore(memory).save(b'{"ANN": [1, 0, 4, 2], "BOB": [0, 1, 2, 4]}')
        stats = book(NvmStore(memory))
        self.assertEqual(stats.record("ANN").games_won, 4)
        self.assertEqual(stats.rank("ANN"), 1)
        stats.record_match(("CAL", "BOB"), (4, 0), 1)
        self.assertEqual(stats.by_recent(NAMES), ("BOB", "CAL", "ANN"))
        self.assertEqual(book(NvmStore(memory)).record("CAL").last_match, 1)


if __name__ == "__main__":
    unittest.main()
