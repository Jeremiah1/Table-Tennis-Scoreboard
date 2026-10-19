import unittest

from tt_scoreboard.name_selection import NameSelection, distinct_names, parse_player_names

NAMES = ("A", "B", "C")


class NameSelectionTest(unittest.TestCase):

    def test_players_start_on_different_names(self):
        selection = NameSelection(NAMES)
        self.assertEqual(selection.current(1), "A")
        self.assertEqual(selection.current(2), "B")

    def test_cycle_wraps_around(self):
        selection = NameSelection(NAMES)
        for expected in ("B", "C", "A"):
            selection.cycle(1)
            self.assertEqual(selection.current(1), expected)

    def test_cycle_back_wraps_around(self):
        selection = NameSelection(NAMES)
        for expected in ("C", "B", "A"):
            selection.cycle_back(1)
            self.assertEqual(selection.current(1), expected)

    def test_cycle_back_undoes_cycle(self):
        selection = NameSelection(NAMES)
        selection.cycle(1)
        selection.cycle_back(1)
        self.assertEqual(selection.current(1), "A")

    def test_cycle_back_skips_name_locked_by_other_player(self):
        selection = NameSelection(NAMES)
        selection.cycle(2)
        selection.toggle_lock(2)  # locks "C"
        selection.cycle_back(1)
        self.assertEqual(selection.current(1), "B")

    def test_locked_player_cannot_cycle_back(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(1)
        selection.cycle_back(1)
        self.assertEqual(selection.current(1), "A")

    def test_cycle_skips_name_locked_by_other_player(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(2)  # locks "B"
        selection.cycle(1)
        self.assertEqual(selection.current(1), "C")

    def test_unlocked_players_may_browse_same_name(self):
        selection = NameSelection(NAMES)
        selection.cycle(1)
        self.assertEqual(selection.current(1), selection.current(2))

    def test_locking_bumps_other_player_off_same_name(self):
        selection = NameSelection(NAMES)
        selection.cycle(1)  # both on "B"
        selection.toggle_lock(1)
        self.assertEqual(selection.current(1), "B")
        self.assertEqual(selection.current(2), "C")

    def test_locked_player_cannot_cycle(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(1)
        selection.cycle(1)
        self.assertEqual(selection.current(1), "A")

    def test_toggle_lock_unlocks(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(1)
        selection.toggle_lock(1)
        self.assertFalse(selection.is_locked(1))
        selection.cycle(1)
        self.assertEqual(selection.current(1), "B")

    def test_complete_when_both_locked(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(1)
        self.assertFalse(selection.complete)
        with self.assertRaises(ValueError):
            selection.selected_names
        selection.toggle_lock(2)
        self.assertTrue(selection.complete)
        self.assertEqual(selection.selected_names, ("A", "B"))

    def test_selection_frozen_once_complete(self):
        selection = NameSelection(NAMES)
        selection.toggle_lock(1)
        selection.toggle_lock(2)
        selection.toggle_lock(1)
        self.assertTrue(selection.complete)

    def test_two_names_only(self):
        selection = NameSelection(("A", "B"))
        selection.toggle_lock(1)
        selection.cycle(2)
        self.assertEqual(selection.current(2), "B")

    def test_rejects_too_few_names(self):
        with self.assertRaises(ValueError):
            NameSelection(("A",))

    def test_rejects_duplicate_names(self):
        with self.assertRaises(ValueError):
            NameSelection(("A", "A", "B"))

    def test_rejects_invalid_player(self):
        with self.assertRaises(ValueError):
            NameSelection(NAMES).cycle(3)


class SharedNameTest(unittest.TestCase):

    def setUp(self):
        self.selection = NameSelection(("A", "B", "GUEST"), shared_names=("GUEST",))

    def test_both_players_can_lock_shared_name(self):
        self.selection.cycle_back(1)  # "GUEST"
        self.selection.toggle_lock(1)
        self.assertEqual(self.selection.current(2), "B")
        self.selection.cycle(2)
        self.assertEqual(self.selection.current(2), "GUEST")
        self.selection.toggle_lock(2)
        self.assertEqual(self.selection.selected_names, ("GUEST", "GUEST"))

    def test_locking_shared_name_does_not_bump_other_player(self):
        self.selection.cycle_back(1)
        self.selection.cycle(2)  # both on "GUEST"
        self.selection.toggle_lock(1)
        self.assertEqual(self.selection.current(2), "GUEST")

    def test_regular_names_still_exclusive(self):
        self.selection.toggle_lock(2)  # locks "B"
        self.selection.cycle(1)
        self.assertEqual(self.selection.current(1), "GUEST")

    def test_shared_name_must_be_in_list(self):
        with self.assertRaises(ValueError):
            NameSelection(("A", "B"), shared_names=("GUEST",))


class DistinctNamesTest(unittest.TestCase):

    def test_different_names_unchanged(self):
        self.assertEqual(distinct_names(("A", "GUEST")), ("A", "GUEST"))

    def test_same_name_numbered_by_player(self):
        self.assertEqual(distinct_names(("GUEST", "GUEST")), ("GUEST 1", "GUEST 2"))


class MenuEntryTest(unittest.TestCase):

    def setUp(self):
        self.selection = NameSelection(("A", "B", "MENU"), menu_names=("MENU",))

    def test_on_menu(self):
        self.assertFalse(self.selection.on_menu(1))
        self.selection.cycle_back(1)
        self.assertTrue(self.selection.on_menu(1))

    def test_menu_entry_cannot_be_locked(self):
        self.selection.cycle_back(1)
        self.selection.toggle_lock(1)
        self.assertFalse(self.selection.is_locked(1))

    def test_both_players_may_browse_to_menu_entry(self):
        self.selection.cycle(2)
        self.selection.cycle_back(1)
        self.assertEqual(self.selection.current(1), "MENU")
        self.assertEqual(self.selection.current(2), "MENU")

    def test_needs_two_player_names_besides_menu(self):
        with self.assertRaises(ValueError):
            NameSelection(("A", "MENU"), menu_names=("MENU",))

    def test_menu_name_must_be_in_list(self):
        with self.assertRaises(ValueError):
            NameSelection(("A", "B"), menu_names=("MENU",))


class StartNamesTest(unittest.TestCase):

    def test_cursors_start_on_given_names(self):
        selection = NameSelection(NAMES, start_names=("C", "A"))
        self.assertEqual((selection.current(1), selection.current(2)), ("C", "A"))

    def test_unknown_start_name_falls_back(self):
        selection = NameSelection(NAMES, start_names=("C", "GONE"))
        self.assertEqual((selection.current(1), selection.current(2)), ("A", "B"))

    def test_same_start_name_only_if_shared(self):
        selection = NameSelection(NAMES, start_names=("C", "C"))
        self.assertEqual((selection.current(1), selection.current(2)), ("A", "B"))
        selection = NameSelection(NAMES, shared_names=("C",), start_names=("C", "C"))
        self.assertEqual((selection.current(1), selection.current(2)), ("C", "C"))


class ParsePlayerNamesTest(unittest.TestCase):

    def test_splits_and_trims(self):
        self.assertEqual(parse_player_names(" A, B ,C,"), ("A", "B", "C"))

    def test_missing_or_empty_uses_default(self):
        self.assertEqual(parse_player_names(None, default=("X", "Y")), ("X", "Y"))
        self.assertEqual(parse_player_names(" , ", default=("X", "Y")), ("X", "Y"))

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            parse_player_names("A,B,A")


if __name__ == "__main__":
    unittest.main()
