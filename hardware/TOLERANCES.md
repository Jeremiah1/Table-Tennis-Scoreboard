<!-- Snapshot for this repository of the author's printer-wide fit tests. Other printers will differ: print the fit coupons first. -->

# Measured tolerances: Prusa MK4S

Fits measured with fit-test prints. Use these before any guess or rule of thumb. Fits that only
matter for one project's parts stay in that project's `AGENTS.md`.

**Valid for:** a Prusa MK4S, 0.4 mm High Flow (HF0.4) nozzle, PLA, 0.20 mm SPEED profile,
15 % infill, walls ≥ 2 mm around the hole. If any of these change (another nozzle or printer, the
structural profile, much thinner walls), print a quick coupon to check before trusting a value.

**Adding a result:** one row per fit, the value in bold, what was tried, and which project and
date it came from. If a new test disagrees with a row, update the row and keep the old test in
the source column.

## Screws (straight into printed plastic, hole axis vertical)

| Fit | Value | Tried / notes | Source |
|---|---|---|---|
| M2.5 self-tapping pilot (Ø5.5 post) | **2.5** | 2.6 slips through; 2.3 jams | button box, 2026-10-22 screw test (2.4–2.7) |
| M3 self-tapping pilot (Ø7.5–8 boss) | **3.0** | 2.7–2.9 too tight; 2.6 won't start. 3.0 is still very tight over 10 mm | button box, 2026-10-22 screw test (2.7–3.0); display enclosure, 2026-10-27 coupon (2.6 failed) |
| M4 clearance (screw slides through) | **4.5** | slides straight through, head sits on a Ø8.6 counterbore | display enclosure, 2026-10-27 coupon |

## Holes, slots and pockets

| Fit | Value | Tried / notes | Source |
|---|---|---|---|
| Vertical holes print small | **~0.12** under on the diameter (0.08–0.17) | measured on Ø24.0–24.6 holes | button box, 2026-10-22 fit test |
| Thin sheet in an upright slot | **+0.25 per side** | 1.52 acrylic; +0.25 / +0.40 / +0.55 tried, +0.25 slides in | display enclosure, 2026-10-27 coupon |
| Rectangular part dropped into a printed cradle | **+0.25 per side** | barrel-jack body and terminal block: good fit | display enclosure, 2026-10-27 jack coupon |
| Pegs in slots | **+0.3 per side** | Ø3.43 pegs drop in, slight wiggle | button box, 2026-10-22 fit test |
| Magnet pocket depth | prints ~0.1 deeper than designed | magnets designed 0.1 proud sat flush | button box, 2026-10-22 fit test |

## Light through plastic

| Fit | Value | Tried / notes | Source |
|---|---|---|---|
| LED window thickness | **0.4** | small LEDs show; dim ones only in dim light. 0.6 barely | button box, 2026-10-22 fit test (0.4–1.0) |

## Not measured yet

- Press fit (stays put), per side
- Horizontal holes (axis along X/Y)
