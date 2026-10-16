import unittest

from tt_scoreboard.scoring import TableTennisMatch


def win_game(match, player):
    while True:
        if match.award_point(player) == player:
            return


class MatchWinnerTest(unittest.TestCase):

    def test_no_winner_at_start(self):
        self.assertIsNone(TableTennisMatch().winner)

    def test_first_to_four_games_wins_by_default(self):
        match = TableTennisMatch()
        for _ in range(3):
            win_game(match, 1)
            win_game(match, 2)
        self.assertIsNone(match.winner)
        win_game(match, 2)
        self.assertEqual(match.winner, 2)
        self.assertEqual(match.games, (3, 4))

    def test_custom_games_to_win(self):
        match = TableTennisMatch(games_to_win=2)
        win_game(match, 1)
        win_game(match, 1)
        self.assertEqual(match.winner, 1)

    def test_points_rejected_after_match_over(self):
        match = TableTennisMatch(games_to_win=1)
        win_game(match, 1)
        with self.assertRaises(ValueError):
            match.award_point(2)

    def test_undo_reopens_finished_match(self):
        match = TableTennisMatch(games_to_win=1)
        win_game(match, 1)
        match.undo_last_point()
        self.assertIsNone(match.winner)
        self.assertEqual(match.points, (10, 0))

    def test_games_to_win_must_be_positive(self):
        with self.assertRaises(ValueError):
            TableTennisMatch(games_to_win=0)


if __name__ == "__main__":
    unittest.main()
