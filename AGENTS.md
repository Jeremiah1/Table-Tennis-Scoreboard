# Table Tennis Scoreboard

Status: **V1 complete** (2026-11-05). The wall-hook hanging hasn't been tried yet.

## Layout
- `README.md`: the build guide and user manual for people. Keep it complete enough that someone can
  rebuild the project from it alone.
- `src/`, `tests/`, `deploy.sh`: CircuitPython firmware for the scoreboard and the remotes.
- `hardware/adafruit-display-enclosure/`, `hardware/adafruit-button-enclosure/`: OpenSCAD designs. Each
  has its own `AGENTS.md` with components, measurements and decisions: read it before changing a design.
- `hardware/stl/`: ready-to-print STLs. Re-export them when a design changes.
- `hardware/TOLERANCES.md`: fits measured on the author's printer.

## Working here
- Tests: `python3 -m unittest discover -s tests -t .`
- "Deploy" means `./deploy.sh scoreboard` or `./deploy.sh remote --side left|right`.
- This repository is public: keep out player names, Wi-Fi details, home paths and personal schedules.
