# Adafruit 128x64 LED Matrix Enclosure

A wall-mounted enclosure for the Adafruit 128x64 2 mm pitch RGB matrix. It hides the wiring and
the Matrix Portal S3 on the back, and hangs on two 3M Command hooks stuck to the wall, so
the display can be lifted off and put back many times.

## Status
**Complete, V1 (2026-11-05).** All parts are printed and assembled, and the sheet is cut and fits its
grooves. Not tested yet: hanging it on the wall hooks.

## For AI assistants
- The build guide for people is the repository's top-level `README.md`. This file is the design record:
  components, measurements, decisions.
- `scad-render`, `mk4s-slice` and the `3d-print-design` skill are the author's local tools (optional;
  OpenSCAD 2021.01 + BOSL2 is all the design needs). Where they exist, use the skill's `SKILL.md` for the
  design loop, design rules and OpenSCAD conventions.
- Generated files go in `out/<design>/<part>/` (gitignored). Render and view the PNGs before slicing.
- After changing a design, re-render its parts and update the matching file in `../stl/`.

## Components
Coordinate convention: panel viewed **from the back**, Matrix Portal S3 on the left. "Left/right/top/bottom edge" distances use that view.

| Part | Source | Key dimensions (mm) | Measured? |
|---|---|---|---|
| 128x64 RGB LED Matrix, 2 mm pitch (#6484) | https://www.adafruit.com/product/6484 | 256 (product page, too long for calipers; the model derives 254.47 from the hole measurements below) × 128.07 (measured), square corners, 8 threaded mounting holes in the flat back, 2 near each edge, mirrored both ways. Centers (measured to hole edge + 1.7): top/bottom-edge holes 93.7 from left/right edge and 10.1 from top/bottom edge; left/right-edge holes 34.0 from top/bottom edge and 6.5 from left/right edge. **Left/right, remeasured 2026-11-02:** right half 94.57 (top/bottom-edge holes) and 7.62 (end holes) from the right edge (outside jaws from the edge to the far side of an M4 screw threaded into the hole, minus half its 3.86 thread); across the middle the two top-edge holes are 66.2 apart (inside jaws 69.6 − 3.4). The 93.7 / 6.5 were edge readings by eye, ~1 mm short. The left tray uses them and fits (its pattern spacing is right), so the model's x = 0 is where that tray puts the left edge and `panel_w` = 93.7 + 66.2 + 94.57 = 254.47 is derived, not measured. Top-edge hole right of the middle: 9.72 from the top edge by the screw method (model 10.1); the first right tray lined up in y, so y stays. The top/bottom distances come from hole-to-hole spacing (calipers' inside jaws across the far sides of a pair, minus the 3.4 hole: end pair 60.0 apart, middle pair 107.85, 2026-10-29); the earlier edge-to-hole readings (9.0 / 33.1) were ~1 mm off. M4 threads (an M4 screw threads in by hand, 2026-10-27). Depth ≥ 10 (an M3×10 sank fully), 254 g. 14.6 thick front to back, back is flat (measured). Sticking out of the back: Matrix Portal S3; 4-pin power connector (8.5 wide × 15.85 tall, center 63.0 from top and 108.2 from right; 12 proud of the back with cable plugged in; cable leaves toward the right edge; stays plugged in permanently, needs clearance only, no access); two nubs, Ø3.05. Nub centers: nub 1 63.23 from left, 10.43 from top; nub 2 63.26 from right, 10.38 from bottom (measured to nub edge + 1.525 radius). Nub height 3.0 (measured). Diagonally opposite, 180° symmetric. LEDs run right to the edge: front border 0 (measured) | partly |
| Matrix Portal S3 (#5778) | https://www.adafruit.com/product/5778 | 63.6 × 44.3 × 20.0 (product page). Plugged into the panel HUB75 input: overhangs the left edge by 28, board top 41.4 from panel top (so 63.6 runs horizontally, 44.3 vertically), tallest point 15 above the panel back = the HUB75 socket at the right end of the board, inside the panel outline (measured). USB-C faces left, in the board lower-left corner, center ~79.2 from panel top; measured from the LED face (panel face down on a table): board bottom 16.2, highest part on the left edge (USB-C or button) 21.7, i.e. 1.6 to 7.1 above the panel back. Three buttons face left in a column above the USB-C; reset must stay reachable (button positions VERIFY). Power wires leave to the right, stay within the panel outline, and are lower than the board top. | partly |
| Female DC adapter, 2.1 mm jack to screw terminal (#368), wired to the panel power cable | https://www.adafruit.com/product/368 | Measured 2026-10-27, terminal end to nose tip: total 37.4 = terminal block ~4 (model uses the rest, 3.7) + rectangular body 9.6 (14 wide × 11.8 tall) + 6–7 thin stepped squares, each smaller, 12.5 + Ø10 cylindrical nose 11.6. Terminal block 10.15 × 10.15. (Earlier 5.2 / 9.4 / 3.2 step / 19.86 nose were wrong.) Mounted with the nose pointing out the right end (back view), wires leave to the left inside the shell. Power supply plug outer diameter ~11 (measured). | partly |
| Clear front sheet (slides in from the top) | bought 10 × 8 in, 0.060" acrylic (the only size/thickness available); cut the 8 in side down to about 133.1 mm (flush with the frame top) | length = panel − 1.55 (measured against the panel) × ~133.1 × 1.52 (thickness measured) | yes |
| M4 × 12 mm screws | user has 10 (no M4 × 10 available) | Head Ø8.0 × 3.5 tall (measured). Through the 3 mm floor they go ~9 mm into the panel | yes |
| M3 × 10 mm screws | user has 5 | M3 slides freely into the panel holes, so they do not grip | yes |
| M2.5 × 12 mm screws | user has 5 | | no |
| 3M Command J-hooks (2) | store (smallest available) | Wall to J tip 20, J thickness 4.8, nook to tip ~17, base 21.3 wide × 30 tall, base 4.5 thick incl. strip (measured). Stand-off 5.3 → bottom bumpers ~5 mm. J width VERIFY (dummy only) | yes |

## Measured tolerances (this project's parts only)
Printer-wide fits (screw pilots, clearances, slots, LED windows) are in `../TOLERANCES.md`.

Used here: M4 clearance 5.0 + Ø9.0 counterbore (4.5 / 8.6 slide fine, the extra gives ±0.5 for hole-position error), M3 pilot 3.0 (2.6 failed on the 2026-10-27 coupon), sheet slot +0.25 per side.

| Fit | Value | Date / test |
|---|---|---|
| Acrylic sheet groove (1.52 sheet) | **+0.25 per side** (notch 1 of +0.25 / 0.40 / 0.55) | 2026-10-27 fit-test coupon |
| Barrel-jack cradle | body and terminal block: good fit at +0.25 per side. Notched wall was misplaced (wrong step length) in v1 | 2026-10-27 jack coupon |
| Hole spacing by hand | measure hole to hole (inside jaws across the far sides of two holes, minus one hole diameter), not edge to hole by eye: edge readings were ~1 mm off per hole. On a printed part the jaw tips catch the counterbore, not the screw hole. Edge to hole: thread an M4 screw halfway in, outside jaws from the panel edge to the far side of the screw, minus half the thread (3.86) | 2026-10-29 left tray; 2026-11-02 right tray |
| Barrel-jack cradle v2 (notched wall 11.6 from the outer end, body + steps pocket 22.1 + 0.4, tongue 0.25 per side) | **perfect fit** | 2026-10-28 jack coupon v2 |

## Decisions
- 2026-10-26: Wall mount is two store-bought 3M Command hooks (model to be chosen and measured).
  The back of the enclosure has recessed hook pockets, so the hooks are hidden and the frame sits
  close to the wall. Slots are wide sideways to allow for hook-spacing error. A printed or paper
  spacing template helps place the hooks level. (This replaced an earlier printed-cleat plan:
  the user preferred buying hooks.)
- 2026-10-26: The LEDs run to the panel edge (no border), so the bezel must not overlap the face.
  The frame wall wraps the panel edge and stands a few mm proud of the LED face. A groove in that
  lip (bottom + both sides, open at the top) holds the acrylic sheet just in front of the LEDs.
  The panel is held by screws from the back, not by a front lip.
- 2026-10-26: Panel holes are most likely M4 (test-fit one screw before buying a pack). Use M4 × 10 screws (user to buy) through a ~3 mm back wall, which gives ~7 mm thread engagement.
- 2026-10-26: Powered by a separate 5 V adapter. The enclosure holds the barrel jack firmly so
  it can be plugged and unplugged without strain on the panel.
- 2026-10-26: Landscape orientation, power cable exits from the side.
- 2026-10-27: Left wing extends 28.5 past the panel edge (28 Portal overhang + 0.5). No air gap: its end wall has a window as tall as the Portal edge (~46), so the Portal edge sits flush in the opening and the USB-C and three buttons are reachable directly.
- 2026-10-27: Balanced look: equal 28.5 wings on both ends (~314 wide overall). The jack sits in the right wing.
- 2026-10-27: Barrel jack sits on the right edge (back view), where the panel power cable already points. The Portal and its USB-C stay on the left edge (back view). The wire to the jack is long enough to reposition it.
- 2026-10-26: The enclosure is wider than the 250 mm bed, so it prints as two halves joined at the center.
- 2026-10-27: Split into 4 prints: `back_left`/`back_right` trays and `end_left`/`end_right` wings
  (`enclosure.scad`). Reasons: (1) the panel can't go in from the front with the Portal attached,
  because the Portal overhang would hit the wing front, so it drops into the back trays from the
  front instead, and the wings go on afterward; (2) a top slot for the sheet can't be printed in a
  one-piece shell without a long unsupported bridge. The trays own the top/bottom walls: the bottom
  wall has the groove, and the top wall stops behind the sheet so the sheet slides in from the top.
  The wings own the side grooves. The trays screw to the panel (8 × M4 × 10), and each wing screws to
  its tray (2 × M3 × 10, from the back). The halves butt at the seam, with the panel as the backbone.
- 2026-10-27: Hook pockets are closed boxes (1.2 floor) so nothing inside shows from the back; the user wants a "professional", fully closed back. Hook depth limit is ~16.8 mm from the wall. Only the screw heads and pocket mouths are visible on the back.
- 2026-10-27: Sheet size is fixed in advance (262 × 131.8 mm) so the store can cut it. The side grooves are 3.65 deep, so a cut that is off by up to ±1/16 in still fits with ≥1.75 mm behind the lip. Sheet thickness only sets the groove width.

- 2026-10-27: **10 in sheet, end columns hidden.** The only sheet available is 10 × 8 in, 0.060" (1.52)
  thick: 254 long vs the 256.1 panel, so it can't reach past the panel edges. Each wing gets a
  1.2 mm lip that reaches 2.2 onto the LED face (`hide_w`), covering the outermost LED column on each
  side (126 of 128 columns show), with a stop behind it that keeps the sheet centred
  (`sheet_play` 0.2 per end). About 1.15 of sheet sits behind each lip (0.95 if pushed to one side),
  so measure the sheet and the panel with the same ruler and set `sheet_w` before printing the wings.
- 2026-10-27: Sheet measured against the panel: 1.55 shorter (`sheet_short`; ends flush on one side,
  calipers at the other; a tape measure read ~10 1/8 vs 10 1/16 in, too coarse). `sheet_play` 0.3 per end.
  Sheet behind each lip: 1.43 centred, 1.13 if pushed to one side. Flush on one end, the sheet leaves
  the last column uncovered at the other, so the lips hiding the outer columns (126 of 128 show) stay.
  Supersedes the 262 mm store-cut sheet and the deep side grooves.
- 2026-10-27: M4 × 12 screws (M4 × 10 unavailable): ~9 mm into the panel; counterbore Ø8.6 for the 8.0 head.
- 2026-10-27: Tray seam moved 20 mm left of centre (`x_seam`), to split the print time at the normal
  0.20 SPEED profile: back_right ~2 h 14 m, back_left
  ~1 h 46 m. Quality over speed: no draft layers.
- 2026-10-27: **Hooks: stand-off, not flush** (supersedes the 16.8 mm closed-pocket limit). The 20 mm
  hooks can't fit a closed pocket over the panel, so the enclosure stands off the wall by the base
  thickness + 0.8 (`standoff`), with two stick-on bumpers that tall at the bottom of the back. Each
  pocket: a 36 wide opening below a solid catch bar (`bar_t` deep, fills the J gap) and a slot behind
  the bar for the J tip; closed ceiling, so nothing shows. Hang: hold high, push back, lower ~19.
  Remove: lift ~19, pull. Can't come off without lifting (checked by sweeping a hook dummy).
  User priority: secure and easy to hang/remove; flush to the wall doesn't matter.
- 2026-10-27: Coupon sheet test changed to upright slots cut from the top (the old flat grooves left
  32 mm of plastic overhanging in mid-air).
- 2026-10-27: The left tray and jack coupon v2 print together; the right tray (jack holder) waits
  until the v2 coupon passes.
- 2026-10-28: **Color: white PLA for all enclosure parts** (wall is baby blue; white frames the black
  panel like a mat and blends with the wall). Use the same brand/spool color for every part
  (~234 g for the left tray + coupon, wings and right tray). Known trade-off: white PLA lets light
  through, so the outer LED column may glow through the 1.2 mm side lips, and edge rows may glow into
  the top/bottom walls. The outer columns stay lit for now. If the glow looks ugly or distracting
  once assembled, switch the outer columns (1 and 128) off in firmware, not in the design.
- 2026-10-29: **Portal ledge in the left wing.** The board wobbles toward the LED face / the wall in its
  HUB75 socket. The left wing's window bottom is now a ledge under the board edge at `portal_ledge_z`
  (17.5 from the LED face), so the board edge is held between the ledge and the tray's tab with
  `portal_play` 0.2. The ledge is the wing's end wall under the board (~1.9 deep); the outer 0.5 stays
  cut down to 15.5 for a USB-C plug. Measured on the printed left tray with the panel face down
  (`portal_check` drawing): board edge 5.2 thick, underside to button tops (`portal_edge_t`; the old
  `portal_edge_z1 - portal_z0` gives 5.5); the button tops rest on the tab even face down (the board sags onto it; the tab does not push it up, user confirmed), so the board
  sits ~1.5 higher than the earlier 16.2 reading (underside ~17.7); tray back face 33.3 above the LED face
  (model 33.4); the buttons stick out slightly past the tab's outer face (too small to measure; no wing
  material there, the window is open); tab 45.95 long (model 45.9), board edge 44.6 (product page 44.3),
  tab overhangs each end of the board by ~0.7–0.8, the wing window by another 0.2. `portal_dummy` still
  uses the old 16.2 / 21.7, so it overlaps the ledge in `collisions` (expected). Goal (user): wing + tab hold the board snug so it can't wiggle. If it still rattles, shim the ledge with tape rather than reprinting.
- 2026-11-02: **Right tray reprint, holes from measurements.** The first right tray missed by ~2.5 at the
  seam because the left/right hole positions were edge readings by eye. Remeasured with screws in the holes
  (Components). The left tray and both wings stay as printed. The model keeps the left tray's 93.7 / 6.5,
  places the right holes from the right edge (94.57 / 7.62) and derives `panel_w` 254.47 from the span across
  the middle (66.2), so everything on the right (wing, jack, pads, hook pocket) keeps its place relative to the
  panel's right end. `x_seam` is fixed at 108.05 (the printed left tray's end) and the right tray starts 0.4
  after it (`seam_gap`, was 0.2). The tray's wing pads are trimmed 0.2 clear of the wing's end wall and
  top/bottom walls: the full Ø9 pads reached 0.5 into the end wall (the printed left tray still has them; its
  wing went on anyway). Checked: the model's `wings` render is triangle for triangle the printed wings STL,
  and the new right tray has zero overlap with the right wing, the left tray and the panel/jack/sheet dummies
  (manifold boolean). The first right tray, lined up on its own, would also have pushed the right wing
  0.2–1.0 into the panel's right end. Hook spacing is now 126.47 center to center (`panel_w` − 2 × `hook_dx`),
  for the hook template.
- 2026-11-03: **Stepped-bridge counterbores** (`bridged_cbore`, `bridge_layer` 0.2). The trays print back face
  down, so each counterbore floor prints over air, and the bridges crossed the screw hole: the printed trays' M4
  holes were stringy and had to be cut clear with a knife. Now the first layer over each counterbore leaves a slot
  as wide as the hole, the second a square, then the round hole, so no strand crosses the hole. Applied to the M4
  and M3 counterbores in both trays. Checked: counterbore floors sit on
  whole 0.2 layers from the bed (M4 15.8, M3 2.4); cross-sections show slot → square → round.
- 2026-11-03: **Jack rest pad.** On the partial v2 tray the jack body fit the cradle but floated. The body's front
  face rests on the panel back and the right wing's inner wall (wing not on yet), but there was a 4.6 mm gap
  behind it to the back plate, so only the nose (saddle + tongue) held it. Added a pad on the back plate under
  the body (`jack_pad_gap` 0.25, the cradle fit). It's on the bed side when printing and the bottom of the cradle
  during assembly, so the jack still drops in. Checked: no overlap with the jack, panel or right wing dummies.

- 2026-11-05: **Sheet height: flush with the frame top**, about 133.1 mm (supersedes 131.8). At 131.8 the
  edge drew a line across the white top border; flush reads as one clear front. Trim only the hidden bottom
  edge, so the visible top edge stays factory-cut.
- 2026-11-05: **Power:** one 5 V 4 A adapter (Adafruit #1466) runs everything. The panel power cable's forks
  are screwed to the Portal's terminals, and the barrel jack is wired to the same terminals.
- 2026-11-05: **V1 released.** The current `back_left` model has the corrected hole positions, the trimmed wing
  pads and the stepped-bridge counterbores; the author's own printed left tray predates them. The model's
  stop-to-stop space is ~253.5, so a 10 in sheet may need a little sanding on its length.

## Print log
All on a Prusa MK4S, 0.4 mm High Flow nozzle, 0.20 SPEED profile, 15 % infill, no supports, white PLA.

| Part | Time | Result |
|---|---|---|
| Fit-test coupon + jack coupon v1 | 1 h 12 m, on a plate shared with 2 button-box sleds | Jack coupon: body + terminal fit well between the walls, but the notched (shoulder) wall was too close: the step is 26.0 from the terminal end, not 17.8. M4 counterbore OK; M3 pilot 2.6 failed (now 3.0); sheet fits slot 1 (+0.25). |
| Left tray + jack coupon v2 (`left_tray_jack_coupon`) | 2 h 12 m | Jack coupon v2: perfect fit. Tray: the lower two M4 holes sat ~2 mm low (the panel holes are 2 mm closer together top to bottom than modeled), bending the back with all four screws in. Kept this tray (user preference): two upper screws only, or file the two lower holes ~2 mm upward. The model is fixed since, so a new `back_left` has the holes in the right place. |
| Wings (`wings`) | 1 h 45 m, 62.6 g | `end_left`: the Portal ledge holds the board snug, no wiggle, no shim needed. |
| Right tray v1 (`back_right`) | 2 h 17 m | **Didn't fit:** all four M4 holes sat to the right of the panel holes, because the left-to-right positions were edge readings by eye and the errors from both halves add up at the seam. Reprinted (Decisions, 2026-11-02). |
| Right tray v2 (`back_right`) | 2 h 17 m, 89.9 g | One attempt failed partway on a different printer with repeated "Stuck filament detected" (#26101) pauses; the same file settings had printed fine on another MK4S, so the printer was the likely cause. The final print: all four M4 holes line up, and the jack rest pad holds the jack well. |
| Acrylic sheet | hand cut, score and snap | Fits the grooves. |
