import unittest

from tt_scoreboard.scoring import LEFT, RIGHT, TableTennisMatch


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

    def test_games_to_win_must_be_positive(self):
        with self.assertRaises(ValueError):
            TableTennisMatch(games_to_win=0)


class UndoTest(unittest.TestCase):

    def test_undo_reopens_finished_match(self):
        match = TableTennisMatch(games_to_win=1)
        win_game(match, 1)
        match.undo_last_point()
        self.assertIsNone(match.winner)
        self.assertEqual(match.points, (10, 0))

    def test_undo_steps_back_repeatedly(self):
        match = TableTennisMatch()
        for player in (1, 2, 2):
            match.award_point(player)
        match.undo_last_point()
        self.assertEqual(match.points, (1, 1))
        match.undo_last_point()
        match.undo_last_point()
        self.assertEqual(match.points, (0, 0))
        self.assertFalse(match.can_undo)

    def test_undo_restores_previous_game_and_server(self):
        match = TableTennisMatch(first_server=1)
        win_game(match, 2)
        self.assertEqual(match.server, 2)
        match.undo_last_point()
        self.assertEqual(match.games, (0, 0))
        self.assertEqual(match.points, (0, 10))
        for _ in range(10):
            match.undo_last_point()
        self.assertEqual(match.server, 1)

    def test_nothing_to_undo_at_start(self):
        match = TableTennisMatch()
        self.assertFalse(match.can_undo)
        with self.assertRaises(ValueError):
            match.undo_last_point()


class SidesTest(unittest.TestCase):

    def test_player_one_starts_on_the_left(self):
        match = TableTennisMatch()
        self.assertEqual(match.player_on_side(LEFT), 1)
        self.assertEqual(match.player_on_side(RIGHT), 2)

    def test_players_switch_ends_after_each_game(self):
        match = TableTennisMatch()
        win_game(match, 1)
        self.assertEqual(match.player_on_side(LEFT), 2)
        win_game(match, 1)
        self.assertEqual(match.player_on_side(LEFT), 1)

    def test_undoing_game_point_switches_back(self):
        match = TableTennisMatch()
        win_game(match, 1)
        match.undo_last_point()
        self.assertEqual(match.player_on_side(LEFT), 1)

    def test_deciding_game_switches_at_five_points(self):
        match = TableTennisMatch()
        for _ in range(3):
            win_game(match, 1)
            win_game(match, 2)
        self.assertTrue(match.deciding_game)
        self.assertEqual(match.player_on_side(LEFT), 1)
        for _ in range(4):
            match.award_point(2)
        self.assertEqual(match.player_on_side(LEFT), 1)
        match.award_point(2)
        self.assertEqual(match.player_on_side(LEFT), 2)
        # Stays switched for the rest of the game, and switches back on undo.
        for _ in range(5):
            match.award_point(1)
        self.assertEqual(match.player_on_side(LEFT), 2)
        for _ in range(10):
            match.undo_last_point()
        self.assertEqual(match.points, (0, 0))
        self.assertEqual(match.player_on_side(LEFT), 1)

    def test_no_mid_game_switch_outside_deciding_game(self):
        match = TableTennisMatch()
        for _ in range(5):
            match.award_point(1)
        self.assertEqual(match.player_on_side(LEFT), 1)

    def test_finished_match_keeps_final_game_ends(self):
        match = TableTennisMatch(games_to_win=2)
        win_game(match, 1)  # game 2 at swapped ends
        win_game(match, 1)
        self.assertEqual(match.player_on_side(LEFT), 2)

    def test_finished_deciding_game_keeps_mid_game_switch(self):
        match = TableTennisMatch(games_to_win=2)
        win_game(match, 1)
        win_game(match, 2)  # deciding game starts with player 1 left, switches at 5
        win_game(match, 2)
        self.assertEqual(match.player_on_side(LEFT), 2)

    def test_rejects_invalid_side(self):
        with self.assertRaises(ValueError):
            TableTennisMatch().player_on_side(3)


if __name__ == "__main__":
    unittest.main()
