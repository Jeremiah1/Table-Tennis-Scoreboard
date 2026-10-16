# Table Tennis Scoreboard

Board: Adafruit Matrix Portal S3

Firmware: CircuitPython 10.3.1

Library bundle: 10.x-mpy, release 20261003

## Deployment

With the board plugged in and mounted, run:

    ./deploy.sh            # copy the app to CIRCUITPY
    ./deploy.sh --libs     # also copy the required libraries from the local bundle
    ./deploy.sh --dry-run  # preview changes without writing to the board

The script finds the drive by its CIRCUITPY label (override with an argument or `$CIRCUITPY`), mirrors `src/tt_scoreboard/` onto the board, copies `code.py` and removes leftover loose modules from older versions.

To deploy manually, copy the contents of src/ to the root of CIRCUITPY:

- `code.py`: a small launcher. CircuitPython only runs `code.py` from the root of the drive.
- `tt_scoreboard/`: the application package. Updating the app normally means replacing just this folder.

Delete any old loose `.py` files (`scoring.py`, `screens.py`, ...) from the root of CIRCUITPY left over from earlier versions.

Copy the libraries listed in requirements-circuitpython.txt from the bundle's lib/ directory into CIRCUITPY/lib/.
## Usage

1. **Name selection**: the UP button controls player 1 and the DOWN button controls player 2. Tap for the next name, double-tap for the previous name, and hold for 1 second to lock in a name (hold again to unlock). A name locked by one player is skipped for the other, except `GUEST` (last in the list), which both players can pick; two guests appear as `GUEST 1` and `GUEST 2`. Edit `PLAYER_NAMES` in `src/tt_scoreboard/app.py` to change the list.
2. **Match**: press a player's button to award them a point. The match is best of 7 (first to 4 games).
3. **Winner**: the match winner is shown until either button is pressed (after a short guard period) or 10 seconds pass, then the board returns to name selection.

## Tests

The game logic in `src/tt_scoreboard/` (`scoring.py`, `name_selection.py`, `gestures.py`) is hardware-independent and can be tested on desktop Python:

    python3 -m unittest discover -s tests -t .
