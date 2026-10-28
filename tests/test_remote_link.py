import unittest

from tt_scoreboard.remote_link import (
    LOST,
    PRESSED,
    RELEASED,
    ButtonStateSender,
    RemoteButtons,
    RemoteButtonTracker,
    decode,
    encode,
)

TIMEOUT_MS = 500


class ProtocolTest(unittest.TestCase):

    def test_round_trip(self):
        self.assertEqual(decode(encode(2, 0xBEEF, 7, True, 87)), (2, 0xBEEF, 7, True, 87))

    def test_unknown_battery(self):
        self.assertIsNone(decode(encode(1, 1, 1, False))[4])

    def test_battery_is_rounded_and_clamped(self):
        self.assertEqual(decode(encode(1, 1, 1, False, 42.6))[4], 43)
        self.assertEqual(decode(encode(1, 1, 1, False, 101.5))[4], 100)
        self.assertEqual(decode(encode(1, 1, 1, False, -1))[4], 0)

    def test_rejects_foreign_messages(self):
        message = bytearray(encode(1, 1, 1, False))
        self.assertIsNone(decode(b"hello"))
        self.assertIsNone(decode(bytes(len(message))))
        message[0] ^= 0xFF
        self.assertIsNone(decode(bytes(message)))

    def test_rejects_invalid_side(self):
        self.assertIsNone(decode(encode(3, 1, 1, False)))


class ButtonStateSenderTest(unittest.TestCase):

    def setUp(self):
        self.sender = ButtonStateSender(
            side=1, session=5, repeat_count=3, repeat_ms=20, heartbeat_ms=100
        )

    def messages(self, start, end, step=1):
        sent = []
        for now in range(start, end, step):
            message = self.sender.message_due(now)
            if message is not None:
                sent.append((now, decode(message)))
        return sent

    def test_idle_sender_sends_nothing(self):
        self.assertEqual(self.messages(0, 1000), [])
        self.assertTrue(self.sender.idle)

    def test_change_is_repeated_then_heartbeats_while_pressed(self):
        self.sender.set_pressed(True, 1000)
        self.assertFalse(self.sender.idle)
        sent = self.messages(1000, 1250)
        self.assertEqual([now for now, _ in sent], [1000, 1020, 1040, 1140, 1240])
        self.assertTrue(all(message == (1, 5, 1, True, None) for _, message in sent))

    def test_release_is_repeated_then_goes_quiet(self):
        self.sender.set_pressed(True, 0)
        self.messages(0, 50)
        self.sender.set_pressed(False, 50)
        sent = self.messages(50, 500)
        self.assertEqual([now for now, _ in sent], [50, 70, 90])
        self.assertEqual(sent[0][1], (1, 5, 2, False, None))
        self.assertTrue(self.sender.idle)

    def test_unchanged_state_is_ignored(self):
        self.sender.set_pressed(False, 0)
        self.assertEqual(self.messages(0, 100), [])

    def test_announce_repeats_state_with_battery(self):
        self.sender.battery = 64
        self.sender.announce(0)
        sent = self.messages(0, 500)
        self.assertEqual([now for now, _ in sent], [0, 20, 40])
        self.assertTrue(all(message == (1, 5, 0, False, 64) for _, message in sent))
        self.assertTrue(self.sender.idle)


class RemoteButtonTrackerTest(unittest.TestCase):

    def setUp(self):
        self.tracker = RemoteButtonTracker(TIMEOUT_MS)

    def test_first_release_is_adopted_silently(self):
        self.assertEqual(self.tracker.update(1, 4, False, 0), [])

    def test_first_press_from_unknown_session_counts(self):
        self.assertEqual(self.tracker.update(1, 5, True, 0), [PRESSED])

    def test_press_and_release(self):
        self.tracker.update(1, 0, False, 0)
        self.assertEqual(self.tracker.update(1, 1, True, 10), [PRESSED])
        self.assertEqual(self.tracker.update(1, 2, False, 20), [RELEASED])

    def test_repeats_and_heartbeats_are_ignored(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 10)
        self.assertEqual(self.tracker.update(1, 1, True, 30), [])
        self.assertEqual(self.tracker.update(1, 1, True, 130), [])

    def test_out_of_order_packet_is_ignored(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 10)
        self.tracker.update(1, 2, False, 20)
        self.assertEqual(self.tracker.update(1, 1, True, 30), [])

    def test_fully_lost_tap_is_rebuilt(self):
        self.tracker.update(1, 0, False, 0)
        self.assertEqual(self.tracker.update(1, 2, False, 50), [PRESSED, RELEASED])

    def test_lost_release_and_press_rebuilt(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 10)
        self.assertEqual(self.tracker.update(1, 3, True, 50), [RELEASED, PRESSED])

    def test_counter_wraparound(self):
        self.tracker.update(1, 0xFFFF, False, 0)
        self.assertEqual(self.tracker.update(1, 0, True, 10), [PRESSED])

    def test_new_session_cancels_stale_press(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 10)
        self.assertEqual(self.tracker.update(2, 1, False, 20), [LOST])

    def test_timeout_cancels_silent_press(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 0)
        self.assertIsNone(self.tracker.check_timeout(TIMEOUT_MS))
        self.assertEqual(self.tracker.check_timeout(TIMEOUT_MS + 1), LOST)
        self.assertIsNone(self.tracker.check_timeout(TIMEOUT_MS + 2))

    def test_heartbeat_keeps_press_alive(self):
        self.tracker.update(1, 0, False, 0)
        self.tracker.update(1, 1, True, 0)
        self.tracker.update(1, 1, True, 400)
        self.assertIsNone(self.tracker.check_timeout(800))

    def test_released_button_never_times_out(self):
        self.tracker.update(1, 0, False, 0)
        self.assertIsNone(self.tracker.check_timeout(10000))


class RemoteButtonsTest(unittest.TestCase):

    def test_routes_messages_by_side(self):
        buttons = RemoteButtons(TIMEOUT_MS)
        self.assertEqual(buttons.receive(encode(2, 9, 1, True), 0), [(2, PRESSED)])
        self.assertEqual(buttons.receive(encode(1, 9, 1, True), 0), [(1, PRESSED)])
        self.assertEqual(buttons.check_timeouts(TIMEOUT_MS + 1), [(1, LOST), (2, LOST)])

    def test_battery_is_tracked_by_side(self):
        buttons = RemoteButtons(TIMEOUT_MS)
        self.assertIsNone(buttons.battery(1))
        buttons.receive(encode(1, 9, 0, False, 55), 0)
        buttons.receive(encode(2, 9, 0, False, 12), 0)
        self.assertEqual((buttons.battery(1), buttons.battery(2)), (55, 12))

    def test_unknown_battery_keeps_last_reading(self):
        buttons = RemoteButtons(TIMEOUT_MS)
        buttons.receive(encode(1, 9, 0, False, 55), 0)
        buttons.receive(encode(1, 9, 1, True), 10)
        self.assertEqual(buttons.battery(1), 55)

    def test_announce_is_not_a_press(self):
        sender = ButtonStateSender(side=1, session=3)
        sender.battery = 80
        buttons = RemoteButtons(TIMEOUT_MS)
        sender.announce(0)
        events = []
        for now in range(0, 200):
            message = sender.message_due(now)
            if message is not None:
                events += buttons.receive(message, now)
        self.assertEqual(events, [])
        self.assertEqual(buttons.battery(1), 80)

    def test_ignores_foreign_messages(self):
        self.assertEqual(RemoteButtons(TIMEOUT_MS).receive(b"other", 0), [])

    def test_sender_to_tracker_end_to_end(self):
        sender = ButtonStateSender(side=2, session=3)
        buttons = RemoteButtons(TIMEOUT_MS)
        events = []
        for now in range(0, 400):
            if now == 50:
                sender.set_pressed(True, now)
            if now == 120:
                sender.set_pressed(False, now)
            message = sender.message_due(now)
            if message is not None:
                events += buttons.receive(message, now)
            events += buttons.check_timeouts(now)
        self.assertEqual(events, [(2, PRESSED), (2, RELEASED)])


if __name__ == "__main__":
    unittest.main()
