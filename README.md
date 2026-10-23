# Table Tennis Scoreboard

A 128x64 RGB LED matrix scoreboard with a wireless arcade-button remote mounted at each end of the table.

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
    ./deploy.sh remote --side left      # QT Py remote for the left end of the table
    ./deploy.sh remote --side right     # QT Py remote for the right end
    ./deploy.sh remote --side left --dry-run  # preview without writing

The script finds the drive by reading `Board ID` in each mounted drive's `boot_out.txt`, so it refuses to put remote code on the Matrix Portal or vice versa. It mirrors `src/tt_scoreboard/` onto the board and copies that board's `code.py`. For remotes it also writes `TT_SIDE = "left"` (or `"right"`) to the board's `settings.toml`, keeping any other settings (and removing the old `TT_PLAYER` setting). Override the drive with a final argument or `$CIRCUITPY`.

### Player names

The names are kept out of the repository. Copy `players.example.txt` to `players.txt` (ignored by git) and list one name per line, 8 characters max. `./deploy.sh scoreboard` saves them on the board as `TT_PLAYERS = "NAME1,NAME2,..."` in its `settings.toml`; without a `players.txt` it leaves the board's names as they are. A board with no `TT_PLAYERS` shows `PLAYER 1` to `PLAYER 4`.

A new QT Py first needs CircuitPython installed: use the installer on circuitpython.org for the QT Py ESP32-S3 (pick the variant matching your board: no PSRAM, or 4MB flash/2MB PSRAM). Then plug it in so CIRCUITPY appears, and run the deploy command.

## Remotes

### Wiring

Connect the arcade button's **switch** terminals (the two on the switch body, not the LED terminals) with the quick-connect wires to the Terminal Block BFF:

- one switch terminal to **RX** (GPIO 16, which can wake the board from deep sleep)
- the other switch terminal to **GND**

The pin uses the internal pull-up, so no resistor is needed. The button's LED is not used.

The QT Py ESP32-S3 has no battery charger, so the LiPo needs a charger/connector add-on (such as the LiPo BFF, stacked with the Terminal Block BFF) or an external charger.

### Behavior

- A remote belongs to an end of the table, not to a player, so it can stay mounted while players change ends. A press scores for whoever is at that end.
- On power-up or wake, the QT Py's NeoPixel blinks **blue once for the left side, twice for the right**. Ten fast **red** blinks mean `TT_SIDE` is missing; redeploy with `--side`.
- Each press is broadcast over **ESP-NOW** (no Wi-Fi network needed) and behaves exactly like that side's onboard button: tap, double-tap and hold all work.
- After 10 minutes without a press the remote goes into deep sleep. **The next press only wakes it** (watch for the blue blink); it is not sent to the scoreboard. While plugged into USB, CircuitPython only simulates deep sleep.

### Radio notes

ESP-NOW requires the scoreboard and remotes to be on the same Wi-Fi channel. Neither joins a Wi-Fi network, so they stay on the default channel. Don't set up Wi-Fi (`CIRCUITPY_WIFI_SSID`) on the scoreboard, or it moves to the router's channel and stops hearing the remotes.

Set `REMOTES_ENABLED = False` in `src/tt_scoreboard/app.py` to turn off the radio on the scoreboard.

## Usage

The onboard UP and DOWN buttons on the Matrix Portal always work too: UP is the left side and DOWN is the right side.

1. **Name selection**: the left button picks player 1 (who starts at the left end) and the right button player 2. Tap for the next name, double-tap for the previous name, and hold for 1 second to lock in a name (hold again to unlock). Names are listed most recently played first, and after a match both cursors start on the players who just played, each at the end they finished at. Resting on a name for a second replaces `HOLD=LOCK` with that player's rank, record and win rate (shortened to fit). A name locked by one player is skipped for the other, except `GUEST`, which both players can pick; two guests appear as `GUEST 1` and `GUEST 2`. The last entry, `STATS` (in purple), is a menu item: hold on it to browse the stats. See [Player names](#player-names) to change the list.
2. **Serve**: tap your button to serve first; the serve bars appear around your name. Either player can tap to change it. Once someone is chosen, hold either button for 1 second to start the match.
3. **Match**: press the button at your end of the table to award yourself a point. The match is best of 7 (first to 4 games). Players change ends after every game, and in the deciding game when someone reaches 5 points; the display swaps names, scores and game counts at the same moment, so each half of the board always shows the player at that end.
   - **Undo**: double-tap either button to undo the last point. Repeat to step further back, even into the previous game (sides switch back too). Because a tap has to wait to see if a second tap follows, each point appears about 0.3 s after the press.
4. **Winner**: the match winner is shown until either button is held for 1 second or 30 seconds pass, then the board returns to name selection. Single taps do nothing, so a double tap that registers as one tap can't skip the screen. If the winning point was a mistake, double-tap either button (any time before the board moves on) to undo it and return to the match. Then the winner's and the loser's updated stats cards show for 5 seconds each (any press skips).

## Stats

Every match is recorded when its winner screen is confirmed, so an undone winning point never counts. Guests are not tracked; a named player's match against a guest still counts for them.

- **Leaderboard**: 4 players per page with their match record and match win rate. Players are ranked by `(wins + 2) / (matches + 4)`, as if everyone started with 2 extra wins and 2 extra losses, so one lucky win can't hold first place; ties go to the better game win rate. Players with no matches, and inactive players who haven't played in the last 30 matches, are hidden; their stats are kept, and they return as soon as they play again.
- **Player card**: match and game records with win rates, leaderboard rank and matches played.

Getting there:

- Hold on `STATS` in the name list to browse: tap for the next page, double-tap for the previous one, hold to go back (it also goes back after a minute untouched).
- After a minute untouched, the name screen cycles through the leaderboard and every card by itself. The first press goes back to the name screen, keeping any names already picked.

Reset: hold both buttons for 5 seconds on any stats screen (two people, or the board's UP and DOWN buttons), then hold both again for 3 seconds to confirm. Any other press cancels.

Stats are kept in the board's non-volatile memory, not on the CIRCUITPY drive, so deploying never touches them. They're stored by name: a player removed from `players.txt` is hidden, and their stats return if the name is added back.

## Tests

The logic in `src/tt_scoreboard/` that doesn't touch hardware (`scoring.py`, `name_selection.py`, `gestures.py`, `remote_link.py`, `stats.py`) can be tested on desktop Python:

    python3 -m unittest discover -s tests -t .

## License

Released under the [MIT License](LICENSE): free for anyone to use, copy, modify and share.
