# Table Tennis Scoreboard

A 128x64 RGB LED matrix scoreboard with a wireless arcade-button remote for each player.

| Part | Hardware |
| --- | --- |
| Scoreboard | Adafruit Matrix Portal S3 + 128x64 RGB LED Matrix Panel |
| Remotes (x2) | Adafruit QT Py ESP32-S3, Terminal Block BFF, Large Arcade Button, 0.187" quick-connect wires, LiPo battery |

Firmware: CircuitPython 10.3.1 on every board

Library bundle: 10.x-mpy, release 20261003 (scoreboard only; the remotes use built-in modules)

## Layout

    src/
    ├── scoreboard/code.py   launcher for the Matrix Portal
    ├── remote/code.py       launcher for a QT Py remote
    └── tt_scoreboard/       shared package (copied to every board)

CircuitPython only runs `code.py` from the root of CIRCUITPY, so each board gets its own small launcher plus the `tt_scoreboard` package.

## Deployment

Plug in one board at a time (or pass the mount point), then run:

    ./deploy.sh scoreboard              # Matrix Portal: copy the app
    ./deploy.sh scoreboard --libs       # ...and the libraries from the local bundle
    ./deploy.sh remote --player 1       # QT Py remote for player 1
    ./deploy.sh remote --player 2       # QT Py remote for player 2
    ./deploy.sh remote --player 1 --dry-run   # preview without writing

The script finds the drive by reading `Board ID` in each mounted drive's `boot_out.txt`, so it refuses to put remote code on the Matrix Portal or vice versa. It mirrors `src/tt_scoreboard/` onto the board and copies that board's `code.py`. For remotes it also writes `TT_PLAYER = N` to the board's `settings.toml`, keeping any other settings. Override the drive with a final argument or `$CIRCUITPY`.

A new QT Py first needs CircuitPython installed: use the installer on circuitpython.org for the QT Py ESP32-S3 (pick the variant matching your board: no PSRAM, or 4MB flash/2MB PSRAM). Then plug it in so CIRCUITPY appears, and run the deploy command.

## Remotes

### Wiring

Connect the arcade button's **switch** terminals (the two on the switch body, not the LED terminals) with the quick-connect wires to the Terminal Block BFF:

- one switch terminal to **A0**
- the other switch terminal to **GND**

The pin uses the internal pull-up, so no resistor is needed. The button's LED is not used.

The QT Py ESP32-S3 has no battery charger, so the LiPo needs a charger/connector add-on (such as the LiPo BFF, stacked with the Terminal Block BFF) or an external charger.

### Behavior

- On power-up or wake, the QT Py's NeoPixel blinks **blue once for player 1, twice for player 2**. Ten fast **red** blinks mean `TT_PLAYER` is missing; redeploy with `--player`.
- Each press is broadcast over **ESP-NOW** (no Wi-Fi network needed) and behaves exactly like that player's onboard button: tap, double-tap and hold all work.
- After 10 minutes without a press the remote goes into deep sleep. **The next press only wakes it** (watch for the blue blink); it is not sent to the scoreboard. While plugged into USB, CircuitPython only simulates deep sleep.

### Radio notes

ESP-NOW requires the scoreboard and remotes to be on the same Wi-Fi channel. Neither joins a Wi-Fi network, so they stay on the default channel. Don't set up Wi-Fi (`CIRCUITPY_WIFI_SSID`) on the scoreboard, or it moves to the router's channel and stops hearing the remotes.

Set `REMOTES_ENABLED = False` in `src/tt_scoreboard/app.py` to turn off the radio on the scoreboard.

## Usage

The onboard UP and DOWN buttons on the Matrix Portal always work too: UP is player 1 and DOWN is player 2.

1. **Name selection**: tap for the next name, double-tap for the previous name, and hold for 1 second to lock in a name (hold again to unlock). A name locked by one player is skipped for the other, except `GUEST` (last in the list), which both players can pick; two guests appear as `GUEST 1` and `GUEST 2`. Edit `PLAYER_NAMES` in `src/tt_scoreboard/app.py` to change the list.
2. **Match**: press a player's button to award them a point. The match is best of 7 (first to 4 games).
3. **Winner**: the match winner is shown until either button is pressed (after a short guard period) or 10 seconds pass, then the board returns to name selection.

## Tests

The logic in `src/tt_scoreboard/` that doesn't touch hardware (`scoring.py`, `name_selection.py`, `gestures.py`, `remote_link.py`) can be tested on desktop Python:

    python3 -m unittest discover -s tests -t .
