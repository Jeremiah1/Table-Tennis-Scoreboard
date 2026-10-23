"""Firmware for a wireless arcade-button remote (QT Py ESP32-S3).

The arcade button's switch is wired between BUTTON_PIN and GND on the
Terminal Block BFF. The remote is mounted at one end of the table, and which
end comes from TT_SIDE ("left" or "right") in the board's settings.toml,
written by deploy.sh. A press scores for whichever player is at that end.
"""
import alarm
import board
import digitalio
import espnow
import keypad
import os
import supervisor  # pyright: ignore[reportMissingModuleSource]  (CircuitPython built-in; stubs only)
import time
import wifi
from neopixel_write import neopixel_write
from tt_scoreboard.gestures import ticks_diff
from tt_scoreboard.remote_link import ButtonStateSender

BUTTON_PIN = board.RX
# Deep sleep after this long without a press. The press that wakes the remote
# only wakes it; it is not sent to the scoreboard.
IDLE_SLEEP_MS = 10 * 60 * 1000
LOOP_DELAY_S = 0.002

BROADCAST_MAC = b"\xff\xff\xff\xff\xff\xff"
# NeoPixel colors (GRB byte order).
SIDE_COLOR = (0, 0, 40)
ERROR_COLOR = (0, 40, 0)

SIDES = ("left", "right")

def configured_side():
    """Return 1 for the left end of the table, 2 for the right."""
    side = str(os.getenv("TT_SIDE", "")).strip().lower()
    if side not in SIDES:
        raise ValueError(
            'Set TT_SIDE = "left" or "right" in settings.toml (deploy.sh remote --side SIDE)'
        )
    return SIDES.index(side) + 1

def blink(color, count, on_s=0.15, off_s=0.15):
    """Blink the onboard NeoPixel, then switch its power off to save battery."""
    with digitalio.DigitalInOut(board.NEOPIXEL_POWER) as power, \
            digitalio.DigitalInOut(board.NEOPIXEL) as pixel:
        power.switch_to_output(value=True)
        pixel.switch_to_output()
        for _ in range(count):
            neopixel_write(pixel, bytearray(color))
            time.sleep(on_s)
            neopixel_write(pixel, bytearray(3))
            time.sleep(off_s)
        power.value = False

def deep_sleep_until_pressed():
    # While connected to USB, CircuitPython only simulates deep sleep.
    wake = alarm.pin.PinAlarm(pin=BUTTON_PIN, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake)

def run(side):
    wifi.radio.enabled = True
    radio = espnow.ESPNow()
    peer = espnow.Peer(mac=BROADCAST_MAC)
    radio.peers.append(peer)
    # A random session lets the scoreboard tell a restarted remote from a stale one.
    sender = ButtonStateSender(side, session=int.from_bytes(os.urandom(2), "big"))
    keys = keypad.Keys((BUTTON_PIN,), value_when_pressed=False, pull=True, interval=0.02)
    event = keypad.Event()
    last_activity = supervisor.ticks_ms()
    try:
        while True:
            now = supervisor.ticks_ms()
            while keys.events.get_into(event):
                sender.set_pressed(event.pressed, now)
                last_activity = now
            message = sender.message_due(now)
            if message is not None:
                try:
                    radio.send(message, peer)
                except (OSError, RuntimeError) as error:
                    # The repeats cover an occasional failed send.
                    print("ESP-NOW send failed:", error)
            if sender.idle and ticks_diff(now, last_activity) >= IDLE_SLEEP_MS:
                return
            time.sleep(LOOP_DELAY_S)
    finally:
        keys.deinit()
        radio.deinit()

def main():
    try:
        side = configured_side()
    except ValueError:
        blink(ERROR_COLOR, 10)
        raise
    blink(SIDE_COLOR, side)
    run(side)
    deep_sleep_until_pressed()
