// fit-test.scad: tolerance coupons for the arcade button boxes (one print, several loose pieces).
// Print: as laid out, flat on the bed, white or natural PLA. No supports.
include <BOSL2/std.scad>

/* [Part] */
part = "all"; // [all, holes, posts, windows, magnets, screws]

/* [Button hole] */
coupon_t = 2.0;                               // mm; thinner than the 3 mm lid to save print time
hole_steps = [24.0, 24.2, 24.4, 24.6];        // mm; thread OD measured 23.5-23.7
slot_step = 1;                                // index of the hole that also gets peg slots

/* [Anti-rotation pegs] */
peg_d = 3.43;             // mm, measured: (41.2 outside - 34.35 inside) / 2
peg_r_min = 18.4;         // mm; measured peg-centre radius 18.9 (37.78 / 2), +-0.5
peg_r_max = 19.4;         // mm
peg_clear = 0.3;          // mm per side

/* [Board posts (M2.5)] */
post_dx = 32.8;           // mm, hole centres along the board's length (measured 2026-10-22)
post_dy = 25.15;          // mm, hole centres across the board (measured 2026-10-22)
post_d = 5.5;             // mm, post outer diameter
post_h = 15;              // mm above the plate, same as the box's posts (the M2.5 screws are 12 mm)
pilots = [2.4, 2.5, 2.6, 2.7];  // mm, pilot hole per post, for M2.5 screws (2.0-2.3 too tight, 2026-10-22)

/* [Lid screw bosses (M3)] */
m3_boss_d = 7.5;          // mm, same as the box's corner bosses
m3_boss_h = 10;           // mm above the plate; an M3 x 10 through the 3 mm lid bites ~7
m3_pilots = [2.7, 2.8, 2.9, 3.0];  // mm, pilot hole per boss, for M3 screws

/* [Magnets] */
mag_d = 9.53;             // mm, measured
mag_t = 1.53;             // mm, measured, magnet only
mag_foam = 0.47;          // mm, adhesive foam (measured 2.0 with foam, minus 1.53)
mag_proud = 0.1;          // mm the magnet face sits above the surface, so it touches the steel
mag_clear = 0.15;         // mm per side

/* [LED windows] */
window_steps = [0.4, 0.6, 0.8, 1.0];  // mm thick
window_size = 14;         // mm square

/* [Hidden] */
$fn = 96;
eps = 0.01;
font = "Liberation Sans:style=Bold";
label_size = 5;           // mm cap height-ish
engrave = 0.6;            // mm deep

cell_w = 30;              // plain hole piece width
cell_l = 37;              // plain hole piece length (hole area + label strip)
slot_cell = 52;           // peg-slot piece size
gap = 4;                  // mm between pieces on the bed

// Always show one decimal, so 24.0 reads "24.0", not "24".
function fmt(x) = let(i = floor(x + 0.001), d = round((x - i) * 10)) str(i, ".", d);

module label(txt, size=label_size) {
    linear_extrude(engrave + eps)
        text(txt, size=size, font=font, halign="center", valign="center");
}

// Engrave text into the top face of a plate of thickness t.
module engraved(t) {
    difference() {
        children(0);
        up(t - engrave) children(1);
    }
}

// One button-hole coupon; with_slots adds the two radial peg slots.
module hole_piece(d, with_slots=false) {
    w = with_slots ? slot_cell : cell_w;
    l = cell_l;
    hole_y = l - cell_w / 2;
    engraved(coupon_t) {
        difference() {
            cuboid([w, l, coupon_t], rounding=2, edges="Z", anchor=FRONT+LEFT+BOT);
            translate([w / 2, hole_y, -eps]) cylinder(d=d, h=coupon_t + 2 * eps);
            if (with_slots)
                for (a = [0, 180])
                    translate([w / 2, hole_y, -eps]) zrot(a) peg_slot();
        }
        translate([w / 2, 4.5, 0]) label(fmt(d));
    }
}

// Radial slot that accepts a peg anywhere between peg_r_min and peg_r_max.
module peg_slot() {
    sw = peg_d + 2 * peg_clear;
    hull() {
        translate([peg_r_min, 0, 0]) cylinder(d=sw, h=coupon_t + 2 * eps);
        translate([peg_r_max, 0, 0]) cylinder(d=sw, h=coupon_t + 2 * eps);
    }
}

module holes() {
    xs = [for (i = [0 : len(hole_steps) - 1])
            i * (cell_w + gap) + (i > slot_step ? slot_cell - cell_w : 0)];
    for (i = [0 : len(hole_steps) - 1])
        translate([xs[i], 0, 0]) hole_piece(hole_steps[i], i == slot_step);
}

// Plate with four M2.5 posts at the board's hole spacing; each post has a different pilot.
module posts() {
    plate_t = 1.2;
    pw = post_dx + 18;
    pl = post_dy + 14;
    cx = pw / 2;
    cy = pl / 2;
    corners = [[-1, -1], [1, -1], [-1, 1], [1, 1]];
    engraved(plate_t) {
        difference() {
            union() {
                cuboid([pw, pl, plate_t], rounding=2, edges="Z", anchor=FRONT+LEFT+BOT);
                for (c = corners)
                    translate([cx + c[0] * post_dx / 2, cy + c[1] * post_dy / 2, 0])
                        cylinder(d=post_d, h=plate_t + post_h);
            }
            for (i = [0 : 3])
                translate([cx + corners[i][0] * post_dx / 2, cy + corners[i][1] * post_dy / 2,
                           plate_t])
                    cylinder(d=pilots[i], h=post_h + eps);
        }
        for (i = [0 : 3])
            translate([cx + corners[i][0] * (post_dx / 2 - 9), cy + corners[i][1] * post_dy / 2, 0])
                label(fmt(pilots[i]), 4.5);
    }
}

// Strip of four M3 bosses, one pilot size each, for the lid screws.
module m3_bosses() {
    plate_t = 1.2;
    pitch = 13;
    pw = 4 * pitch;
    pl = 20;
    engraved(plate_t) {
        difference() {
            union() {
                cuboid([pw, pl, plate_t], rounding=2, edges="Z", anchor=FRONT+LEFT+BOT);
                for (i = [0 : 3]) translate([pitch / 2 + i * pitch, 13, 0])
                    cylinder(d=m3_boss_d, h=plate_t + m3_boss_h);
            }
            for (i = [0 : 3]) translate([pitch / 2 + i * pitch, 13, plate_t])
                cylinder(d=m3_pilots[i], h=m3_boss_h + eps);
        }
        for (i = [0 : 3]) translate([pitch / 2 + i * pitch, 4, 0]) label(fmt(m3_pilots[i]), 4);
    }
}

// Frame with thin tiles; hold each over the LEDs to pick the window thickness.
module windows() {
    frame_t = 2;
    cell = window_size + 6;
    n = len(window_steps);
    engraved(frame_t) {
        difference() {
            cuboid([n * cell + 2, cell + 10, frame_t], rounding=2, edges="Z",
                   anchor=FRONT+LEFT+BOT);
            for (i = [0 : n - 1])
                translate([1 + i * cell + 3, 13, window_steps[i]])
                    cube([window_size, window_size, frame_t]);
        }
        for (i = [0 : n - 1])
            translate([1 + i * cell + cell / 2, 5, 0]) label(fmt(window_steps[i]), 4.5);
    }
}

// Block with two magnet pockets (foam side down into the pocket), and a hole to hang a weight from.
module magnet_block() {
    depth = mag_t + mag_foam - mag_proud;
    t = depth + 1.6;
    difference() {
        cuboid([44, 22, t], rounding=2, edges="Z", anchor=FRONT+LEFT+BOT);
        for (x = [11, 27]) translate([x, 11, t - depth]) cylinder(d=mag_d + 2 * mag_clear, h=depth + eps);
        translate([38.5, 11, -eps]) cylinder(d=4, h=t + 2 * eps);
    }
}

holes_w = len(hole_steps) * (cell_w + gap) + slot_cell - cell_w - gap;
row2_y = -(post_dy + 14) - gap;

if (part == "all") {
    holes();
    translate([0, row2_y, 0]) posts();
    translate([post_dx + 18 + gap, row2_y, 0]) windows();
    translate([post_dx + 18 + gap + len(window_steps) * (window_size + 6) + 2 + gap, row2_y, 0]) magnet_block();
}
if (part == "holes") holes();
if (part == "posts") posts();
if (part == "windows") windows();
if (part == "magnets") magnet_block();
if (part == "screws") {
    posts();
    translate([0, post_dy + 14 + gap, 0]) m3_bosses();
}
