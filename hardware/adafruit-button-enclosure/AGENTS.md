# Arcade button boxes (table tennis scoreboard)

Two identical battery-powered boxes, each holding a 60 mm arcade button. A press wakes the
QT Py ESP32-S3, which sends an ESP-NOW broadcast to the LED scoreboard (firmware in `../../src/`).

## Status
**Complete, V1 (2026-11-05).** Printed, assembled, and running the firmware in this repository.

## For AI assistants
- The build guide for people is the repository's top-level `README.md`. This file is the design record:
  components, measurements, decisions.
- `scad-render`, `mk4s-slice` and the `3d-print-design` skill are the author's local tools (optional;
  OpenSCAD 2021.01 + BOSL2 is all the design needs). Where they exist, use the skill's `SKILL.md` for the
  design loop, design rules and OpenSCAD conventions.
- Generated files go in `out/<design>/<part>/` (gitignored). Render and view the PNGs before slicing.
- After changing a design, re-render its parts and update the matching file in `../stl/`.

## Shared names (used in conversation and in `button-box/button-box.scad`)
Each box is held by magnets in the inside corner under the ping pong table, at the player's LEFT
corner, with the button pointing at the floor.
- **Part A** = base, **Part B** = lid (holds the button, faces the floor), **Part D** = board sled
  (the QT Py/BFF screws onto it; it slides in along Wall 4). (Part C, the old table bracket, is gone.)
- **Top** = the base's flat top, pressed against the underside of the tabletop.
- **Wall 1** = against the end apron (player's side). **Wall 2** = against the side apron.
  **Wall 3** = faces the net under the table; USB-C charging opening.
  **Wall 4** = faces the middle of the table; board hangs under it. Windows **W1** (orange CHG
  LED) and **W2** (green DON LED) exist in the design but are off (`led_windows = false`).
- **M1–M6** = magnets: M1–M3 in Wall 1; M4–M6 in Wall 2 (two high, one lower in the middle).
- **S1, S2, S4** = lid screws (S1 at Wall 1/Wall 2, S2 at Wall 2/Wall 3, S4 at Wall 4/Wall 1).
  There is no S3: the board fills the Wall 3/Wall 4 corner.

## Components (per box; 2 of everything)
| Part | Source | Key dimensions (mm) | Measured? |
|---|---|---|---|
| Arcade button, 60 mm, LED unused | [Adafruit 1192](https://www.adafruit.com/product/1192) | Thread M24, measured OD 23.5–23.7. Bezel Ø60.8 (drawing). Cap above bezel underside 14.8. Thread length 29.95. Round nut OD 32.35, thickness 8.73. Lowest point (switch bottom) 54.3 below bezel underside. Switch body 27.7 (along the peg line) × 12.05, centred under the threads, ~2 mm gap below them. Tabs stick out on one peg's side (PEG A); the longest tab with its quick-connect reaches 23 past the switch body, so 36.9 from the axis (an earlier reading gave 35.3; the design uses 36.9 plus 4 mm for the wire bend). Names for the sides: `parts/button-reference.scad` | yes |
| Anti-rotation pegs under bezel | (same) | 2 pegs, Ø3.43; 41.2 outside-to-outside, 34.35 inside-to-inside, so 37.78 centre-to-centre (radius 18.89). Height not measured | yes |
| QT Py ESP32-S3 on Terminal Block BFF | [6495](https://www.adafruit.com/product/6495) | BFF body 43.25 × 21 (straight edges). Corner mounting circles (Ø~5.2) stick out ~4.7 past each long edge, so 30.35 across them. 4 holes Ø~2.5 (M2.5), centres 32.8 × 25.15 (re-measured 2026-10-22 over screw shanks; the first reading, 32.3 × 25.75, didn't line up with the fit-test posts). Pins stick out 2.5 below. USB-C shell 11.7–15.08 above the BFF underside. Stack height 15.5 from BFF underside to QT Py top. QT Py sits crosswise: USB-C centred on a long side, flush with the board edge. Terminal blocks on the short ends; button wires go to GND on one end, A0 on the other | yes |
| LiPo 3.7 V 500 mAh | Adafruit | 37.2 × 30.25 × 4.8, wire exits a 30.25 side | yes |
| MAX17048 fuel gauge | [5580](https://www.adafruit.com/product/5580) | 25.7 × 20.3 × 7.2 (published) plus connector overhang | no // VERIFY |
| USB-C round panel-mount extension | [6069](https://www.adafruit.com/product/6069) | Not used (a cable plugs straight into the QT Py through Wall 3) | — |
| Hardware | hardware store | M3 × 10 screws (10; 3 per box for the lid). M2.5 × 12 screws (10; 4 per box into the 15 mm sled posts, 4 for the fit test). 12 disc magnets (6 N + 6 S faces), 9.53 × 1.53, 2.0 thick with their adhesive foam (foam goes into the pocket). 2× M2 × 12 (spare, unused) | yes |
| Table apron | the ping pong table | Steel (magnets stick), 48.4 tall below the tabletop, ~21 thick, flush with the table edge (no overhang). Inside faces flat and smooth. End apron runs the full width; side apron butts into it at a clear inside corner. No drilling | yes |

QT Py NeoPixel: measured from the BFF holes (H1–H4 as labelled in `parts/bff-reference.scad`:
QT Py up, USB-C edge toward you, H1 bottom-left, counter-clockwise) as 21.7 / 28.0 / 22.7 / 17.7.
Best fit: 3.8 mm toward H1/H4 and 3.9 mm away from the USB-C edge from the board centre, about
8 mm above the hole plane (0.6 mm rms). Not used for a window (it needs code to light).

BFF CHG (orange) LED: on the USB-C edge, just inside the mounting circle of H1. DON (green) LED:
same edge, just inside H2's circle. Estimated, not measured; windows W1/W2 are 10 × 10 to allow
for that.

Still to measure (optional): peg height.

## Measured tolerances (this project's parts only)
Printer-wide fits (screw pilots, clearances, slots, LED windows) are in `../TOLERANCES.md`.

| Fit | Value | Date / test |
|---|---|---|
| Button hole (thread OD 23.7) | **24.0** (prints 23.88; thread passes with a little play) | 2026-10-22 fit test |
| Peg slots (Ø3.43 pegs, r 18.4–19.4, 0.3 clear) | as designed: pegs drop in, slight wiggle, centred | 2026-10-22 fit test |
| LED windows | 0.4 thick: DON and NeoPixel show; CHG shows in dim light (0.6 barely) | 2026-10-22 fit test: 0.4–1.0 |
| Magnet pocket / hold | magnets sat flush, not 0.1 proud as designed. 2 magnets on the vertical apron hold ~113 g (4.0 oz), slip at ~119 g. Box ≈ 150 g (parts weighed 68 g + printed 69 g by slicer + ~13 g gauge, cable, screws, magnets) | 2026-10-22 fit test |

## Decisions
- 2026-10-20: Two boxes, one per player. Button LED not used (no LED wiring, no driver).
- 2026-10-20: Wiring is plug-in or screw terminal only: button switch (COM/NO) to GND + A0
  (GPIO 18) — superseded: now GND + RX, see below; battery → gauge JST-PH → 100 mm JST-PH jumper
  → BFF battery port; gauge STEMMA QT → BFF STEMMA QT (superseded: the firmware reads the gauge on the QT Py's own
  STEMMA QT port, SCL1/SDA1, tested on both remotes 2026-10-28). Charging is over the
  QT Py's own USB-C through the BFF (250 mA default); the panel jack idea was dropped.
- 2026-10-20: Mount the bare BFF on 4 printed posts with M2.5 screws. The snap-on enclosure
  (6505) is kept as a spare. Gives brighter LEDs through the window and direct terminal access.
- 2026-10-21: Box height 60 mm (2 mm floor, 3 mm lid): 58 mm under the bezel vs 54.3 mm
  button depth. Lid gets radial slots for the pegs (tolerant of the uncertain spacing), oriented
  so the switch connector points toward the electronics. Box is rectangular: button end
  ~75–80 mm wide, electronics beyond.
- 2026-10-21: Layout: BFF crosswise near the far end wall, USB-C side facing that wall
  (~25 mm gap for the extension's plug); USB-C panel jack in that wall opposite the port.
  ~15 mm free at each BFF short end for terminal wires. BFF stays out from under the switch
  connector's 35.3 mm reach (they share the bottom ~20 mm). Battery stands on its long edge
  in a slot along a side wall. Estimated outer size ~80 × 130–135 × 60, to confirm in the
  assembly render.
- 2026-10-21: **Compact redesign (supersedes the 130 mm layout above):** 72 × 72 × 62 box that
  hangs on a ping pong table's apron, button facing outward, one box near each player's corner on
  the long sides. Board on sled Part D against Wall 4 (top), mounted upside down so the LEDs face
  window W. Gauge on Wall 1, battery on edge on Wall 2. No USB-C panel mount: a cable plugs into the
  QT Py through an opening in the back, with the box lifted off its bracket. Box slides down onto
  bracket Part C (dovetail rails into G1/G2, 25 mm engagement); Part C clamps the apron's bottom edge
  with a thumbscrew. Concept print times per box: base 1 h 46 m, lid 22 m, bracket 44 m, sled 15 m.
- 2026-10-21: USB-C moved to **Wall 3** so the box charges while mounted (a cable plugs straight
  into the QT Py through an opening in Wall 3). The board's long axis now runs front to back.
  Button wires go to **GND and RX (GPIO 16)**, both on the same terminal row, so only the end
  toward the lid needs wire room. RX = GPIO 16 (CircuitPython pins.c); the user confirmed on
  the real BFF that the RX and GND terminals are on the same end. S3 lid screw removed. Part D's Wall 3 edge sits in a groove in Wall 3.
- 2026-10-21: **Corner mount (supersedes the side bracket):** the box sits in the inside corner
  under the table at each player's left corner (right-handed players tap it with the free left
  hand), top against the tabletop, button pointing down. Held by 4 magnets in Walls 1 and 2 on the
  steel aprons; pressing pushes the box into the tabletop, so the magnets only carry its weight.
  Pull it down to remove. Box 72 × 72 × 60; it hangs ~12 mm below the apron edge, the button cap
  ~27 mm below. Charging: through Wall 3 while mounted, or pull the box off. Battery warning moves
  to the scoreboard display (window W kept only so CHG/DON show while charging). Both boxes are
  identical. Wiring is in the top-level `README.md`.
- 2026-10-21: STEMMA QT cable must be the **100 mm** one (4210): the gauge (Wall 1) and the board
  (Wall 3/Wall 4 corner) are ~55–65 mm apart. The USB-C panel mount (6069) is not needed.
- 2026-10-21: Thin 9.53 × 1.53 magnets are weaker than planned. The foam side goes into the
  pocket so the bare magnet face sits 0.1 mm proud and touches the steel. The fit test gets a
  magnet test block (hang a weight from its hole) to decide between 2 and 3 magnets per wall.
  Fit-test posts are now 15 mm tall to match the box, because the M2.5 screws are 12 mm long.
- 2026-10-21: Window W over the NeoPixel replaced by **W1/W2** over the BFF's CHG and DON LEDs,
  so "charging / full" shows through Wall 4 with no code.
- 2026-10-21: Switch measured. The connector plus wire-bend room would hit Wall 3 if it pointed
  straight at it, so the button is turned 45° (`btn_rot = -45`): the PEG A side, and the
  connector, point at the Wall 2/Wall 3 corner (S2). The lid's peg slots turn with it. No change
  to the box size.
- Concept print times per box (corner version): base 1 h 36 m, lid 21 m, sled 15 m.
- 2026-10-22: **3 magnets per wall** (6 per box, all 12 magnets for both boxes). Fit test: 2 magnets
  hold ~113 g sliding down the apron; the box is ~150 g, so 4 magnets gave only 1.5×, 6 give ~2.2×.
  The middle magnet sits 41 mm below the top, under the gauge and the battery. Pockets made 0.2 mm
  shallower (`mag_proud = 0.3`) because 0.1 came out flush. Button hole 24.0, windows 0.4 (fit test).
- 2026-10-22: **No LED windows.** The box will be printed in a dark colour to hide under the
  table, and dark PLA blocks the LEDs even at 0.4. The only opening is USB-C in Wall 3. Charging
  status: look at the board, or the scoreboard. `led_windows = true` brings W1/W2 back.
- 2026-10-22: **USB-C pad on the sled.** Plugging in the cable tipped the QT Py on its header pins
  (its USB-C end lifts into the 1 mm gap under the sled; 1.42 above the shell). Part D gets a
  6 × 8 mm pad over the USB-C shell that reaches just past the shell top (`usb_pad_press`), so the
  QT Py can't lift. Only the sled changes; the board and the Wall 3 opening stay put.
  Gap measured on box 1 (2026-10-23): ~1.1 (`usb_gap`; hard to measure), so the pad is 1.2 tall (0.1 press: the QT Py is already fully seated, so more would only bend the boards).
- Low-battery indicator (superseded): was the QT Py NeoPixel through a window; now shown on the scoreboard.

## Print log
All on a Prusa MK4S, 0.4 mm High Flow nozzle, 0.20 SPEED profile, 15 % infill, no supports.

| Part | Time | Result |
|---|---|---|
| Fit test (holes, posts, windows, magnets) | ~1 h | results in the tolerance table |
| Screw test (M2.5 posts 2.4–2.7, M3 bosses 2.7–3.0) | 22 m | M2.5 → 2.5, M3 → 3.0; board lines up well enough (posts flex) |
| Box: base + lid + sled, one plate, dark PLA | 2 h 02 m | assembled |
| Sled × 2 with USB-C pad (1.2) | on a shared plate | assembled |
