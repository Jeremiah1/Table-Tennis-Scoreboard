import unittest

from tt_scoreboard.crash_log import CrashLog
from tt_scoreboard.stats import NvmStore


class CountingMemory(bytearray):
    """A bytearray that counts slice writes, like flash wear."""

    writes = 0

    def __setitem__(self, index, value):
        self.writes += 1
        super().__setitem__(index, value)


class CrashLogTest(unittest.TestCase):

    def setUp(self):
        self.memory = CountingMemory(256)

    def test_empty_memory_has_no_report(self):
        self.assertIsNone(CrashLog(self.memory, size=64).load())

    def test_saves_and_loads_report(self):
        CrashLog(self.memory, size=64).save("Crashed after 3 min\nValueError")
        self.assertEqual(CrashLog(self.memory, size=64).load(), "Crashed after 3 min\nValueError")

    def test_new_report_replaces_old(self):
        log = CrashLog(self.memory, size=64)
        log.save("a much longer first report")
        log.save("second")
        self.assertEqual(log.load(), "second")

    def test_same_report_is_not_rewritten(self):
        log = CrashLog(self.memory, size=64)
        log.save("same crash")
        writes = self.memory.writes
        log.save("same crash")
        self.assertEqual(self.memory.writes, writes)

    def test_long_report_keeps_the_end(self):
        log = CrashLog(self.memory, size=64)
        log.save("x" * 200 + "ValueError: the error")
        report = log.load()
        self.assertTrue(report.startswith("...\n"))
        self.assertTrue(report.endswith("ValueError: the error"))
        self.assertEqual(len(report.encode()), 60)

    def test_truncation_does_not_split_characters(self):
        log = CrashLog(self.memory, size=64)
        log.save("é" * 100)
        self.assertEqual(set(log.load()[4:]), {"é"})

    def test_clear(self):
        log = CrashLog(self.memory, size=64)
        log.save("crash")
        log.clear()
        self.assertIsNone(log.load())

    def test_uses_only_the_end_of_memory(self):
        CrashLog(self.memory, size=64).save("z" * 100)
        self.assertEqual(bytes(self.memory[:192]), bytes(192))

    def test_lives_beside_the_stats(self):
        stats = NvmStore(self.memory, size=192)
        stats.save(b'{"matches": 1}')
        CrashLog(self.memory, size=64).save("crash")
        self.assertEqual(stats.load(), b'{"matches": 1}')
        with self.assertRaises(ValueError):
            stats.save(b"s" * 190)
        self.assertEqual(CrashLog(self.memory, size=64).load(), "crash")

    def test_rejects_size_that_does_not_fit(self):
        with self.assertRaises(ValueError):
            CrashLog(self.memory, size=300)


if __name__ == "__main__":
    unittest.main()
