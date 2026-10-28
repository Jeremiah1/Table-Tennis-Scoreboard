"""Firmware for a wireless arcade-button remote (QT Py ESP32-S3).

The arcade button's switch is wired between BUTTON_PIN and GND on the
Terminal Block BFF. The remote is mounted at one end of the table, and which
end comes from TT_SIDE ("left" or "right") in the board's settings.toml,
written by deploy.sh. A press scores for whichever player is at that end.

An optional MAX17048 fuel gauge on the STEMMA QT port reports the battery
charge, which is sent with every message for the scoreboard to show.
"""
import alarm
import board
import busio
import digitalio
import espnow
import keypad
import microcontroller
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
# The remote does very little work, and 80 MHz (the lowest clock the radio
# allows) saves power over the default 240 MHz.
CPU_FREQUENCY_HZ = 80_000_000
# The radio is the biggest drain, so it is only on while there is something to
# send. Restarting it takes about 4 ms, too little to notice. After the last
# send it stays on briefly so the packet goes out before the radio stops.
RADIO_OFF_DELAY_MS = 100
# The charge changes slowly, so the fuel gauge is read on wake and then this often.
BATTERY_READ_MS = 60 * 1000

# MAX17048 I2C address, and its state-of-charge register (percent, in 1/256 steps).
GAUGE_ADDRESS = 0x36
GAUGE_SOC_REGISTER = 0x04

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

class FuelGauge:
    """MAX17048 fuel gauge on the STEMMA QT port, read directly so the remote
    needs no libraries. Without one, percent() returns None.
    """

    def __init__(self):
        try:
            self._i2c = busio.I2C(board.SCL1, board.SDA1)
        except RuntimeError:
            # No pull-ups on the bus: no gauge plugged in.
            self._i2c = None
        self._buffer = bytearray(2)

    def percent(self):
        """The battery charge in percent, or None if it can't be read."""
        if self._i2c is None:
            return None
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto_then_readfrom(GAUGE_ADDRESS, bytes((GAUGE_SOC_REGISTER,)), self._buffer)
        except OSError as error:
            print("Fuel gauge read failed:", error)
            return None
        finally:
            self._i2c.unlock()
        return self._buffer[0] + self._buffer[1] / 256

    def deinit(self):
        if self._i2c is not None:
            self._i2c.deinit()

def deep_sleep_until_pressed():
    # On USB, CircuitPython only simulates deep sleep, unless the board woke
    # from a real deep sleep: then it sleeps for real and drops off USB.
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
    gauge = FuelGauge()
    wifi.radio.enabled = False
    last_activity = last_sent = last_battery_read = supervisor.ticks_ms()
    # Report the charge on wake, before the first press.
    sender.battery = gauge.percent()
    sender.announce(last_activity)
    try:
        while True:
            now = supervisor.ticks_ms()
            if ticks_diff(now, last_battery_read) >= BATTERY_READ_MS:
                sender.battery = gauge.percent()
                last_battery_read = now
            while keys.events.get_into(event):
                sender.set_pressed(event.pressed, now)
                last_activity = now
            message = sender.message_due(now)
            if message is not None:
                wifi.radio.enabled = True
                last_sent = now
                try:
                    radio.send(message, peer)
                except (OSError, RuntimeError) as error:
                    # The repeats cover an occasional failed send.
                    print("ESP-NOW send failed:", error)
            elif (sender.idle and wifi.radio.enabled
                    and ticks_diff(now, last_sent) >= RADIO_OFF_DELAY_MS):
                wifi.radio.enabled = False
            if sender.idle and ticks_diff(now, last_activity) >= IDLE_SLEEP_MS:
                return
            time.sleep(LOOP_DELAY_S)
    finally:
        gauge.deinit()
        keys.deinit()
        radio.deinit()

def main():
    microcontroller.cpu.frequency = CPU_FREQUENCY_HZ
    try:
        side = configured_side()
    except ValueError:
        blink(ERROR_COLOR, 10)
        raise
    blink(SIDE_COLOR, side)
    run(side)
    deep_sleep_until_pressed()
