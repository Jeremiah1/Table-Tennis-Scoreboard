// button-box.scad: arcade-button box held by magnets in the inside corner under a ping pong table,
// button pointing at the floor.
// Print: Part A (base) top face down; Part B (lid) outer face down; Part D (board sled) flat, posts up.
// No supports.
//
// Shared names. Each box sits in the player's LEFT corner, under the tabletop:
//   Part A = base, Part B = lid (holds the button, faces the floor), Part D = board sled.
//   Top = the base's flat top, pressed against the underside of the tabletop.
//   Wall 1 = against the end apron (the player's side). Wall 2 = against the side apron.
//   Wall 3 = faces the net, under the table; has the USB-C charging opening.
//   Wall 4 = faces the middle of the table; the board hangs under it. Optional windows W1 (orange
//   CHG LED) and W2 (green DON LED), off by default.
//   M1-M6 = magnets: M1-M3 in Wall 1; M4-M6 in Wall 2.
//   S1, S2, S4 = lid screws: S1 at Wall 1/Wall 2, S2 at Wall 2/Wall 3, S4 at Wall 4/Wall 1.
//   (There is no S3: the board fills the Wall 3/Wall 4 corner.)
//
// Model axes: X = Wall 1 -> Wall 3, Y = Wall 2 -> Wall 4, Z = top -> lid (downward when mounted).
include <BOSL2/std.scad>
include <../parts/components.scad>

/* [Part] */
part = "assembly"; // [assembly, exploded, xray, base, lid, sled, sled_section, plate, collisions]

/* [Box] */
box_l = 72;           // mm, X: Wall 1 to Wall 3
box_w = 72;           // mm, Y: Wall 2 to Wall 4
box_h = 60;           // mm, Z: top to the lid's outer face
wall = 2.4;           // mm
back_t = 2.4;         // mm, the top (against the tabletop)
lid_t = 3;            // mm
corner_r = 4;         // mm

/* [Button] */
btn_x = 33;           // mm; off-centre toward Wall 1, as far as the bezel allows
btn_rot = -45;        // degrees; the switch connector (PEG A side) points at the Wall 2/Wall 3 corner
btn_hole_d = 24.0;    // mm, fit test 2026-10-22 (prints ~23.88)
peg_slot_r = [18.4, 19.4];  // mm; measured peg-centre radius 18.9, +-0.5
peg_clear = 0.3;      // mm per side

/* [Lid joint] */
lip_h = 2;            // mm, locating lip on the lid
lip_w = 1.6;          // mm
lip_clear = 0.3;      // mm per side  // VERIFY: from fit test
boss_d = 7.5;         // mm, corner screw bosses
m3_pilot = 3.0;       // mm, M3 self-tapping into PLA; screw test 2026-10-22 (tight over 10 mm, ~7 bite here)
m3_clear = 3.4;       // mm, lid holes
pilot_depth = 12;     // mm

/* [Magnets] */
mag_d = 9.53;         // mm, measured
mag_t = 1.53;         // mm, measured, magnet only
mag_foam = 0.47;      // mm, adhesive foam (measured 2.0 with foam, minus 1.53); goes into the pocket
mag_proud = 0.3;      // mm the magnet face sits above the wall; 0.1 came out flush in the fit test
mag_clear = 0.15;     // mm per side
// 3 per wall: 2 magnets held ~113 g on the apron in the fit test; the box is ~150 g.
// The middle one sits lower, below the gauge (Wall 1) and the battery (Wall 2). The apron reaches 48.4.
mag_w1 = [[14, 22], [36, 41], [58, 22]];  // mm, [Y, Z below the top] of M1-M3 on Wall 1
mag_w2 = [[22, 22], [38, 41], [54, 22]];  // mm, [X, Z below the top] of M4-M6 on Wall 2

/* [Board sled (Part D) on Wall 4] */
sled_t = 2;           // mm
sled_x0 = 36;         // mm, X of the sled's Wall 1 edge; its other edge sits in a groove in Wall 3
sled_h = 46;          // mm, Z below the top
sled_clear = 0.3;     // mm per side in the guides
qt_gap = 1;           // mm, QT Py top to the sled
board_cx = 53.9;      // mm, X centre of the board; its USB-C edge faces Wall 3
board_z0 = 4;         // mm, Z of the board's unwired end (near the top)
post_d = 5.5;         // mm, same as the fit-test posts
m25_pilot = 2.5;      // mm, screw test 2026-10-22 (2.6 slips)
usb_open = [14, 9];   // mm, Z x Y opening in Wall 3 for the cable plug  // VERIFY with your cable
// Pad under the sled that presses on the QT Py's USB-C shell, so plugging in a cable can't rock
// the QT Py on its header pins (2026-10-22: it tipped into the gap under the sled).
usb_pad = true;
usb_gap = 1.1;        // mm, measured 2026-10-23 on box 1: sled to the top of the USB-C shell (model said 1.42)
usb_pad_press = 0.1;  // mm past the shell top: just touching (pad 1.2 = 6 layers). 0.3 would bend the boards
usb_pad_w = 8;        // mm, Z; a little narrower than the shell

/* [Windows W1, W2 in Wall 4] */
led_windows = false;  // off: a dark box would hide the LEDs anyway (2026-10-22)
window_t = 0.4;       // mm skin left outside; fit test 2026-10-22
window = [10, 10];    // mm, X x Z, generous because the LED positions are estimates
// The BFF's CHG and DON LEDs sit on the USB-C edge, just inside the mounting circles of H1 and H2
// (holes as labelled in parts/bff-reference.scad). Board frame offsets from the board centre:
// 9.5 toward the USB-C edge, 13 along the board toward H1 (CHG) or H2 (DON).  // VERIFY roughly
led_u = 9.5;
led_v = 13;

/* [Gauge on Wall 1, battery on Wall 2] */
gauge_y = 23.15;      // mm
batt_x = 14;          // mm
batt_y = 5.1;         // mm; clears the magnet pads on Wall 2
rib_h = 12;           // mm

/* [Table (for the views only)] */
apron_h = 48.4;       // mm, measured
apron_t = 21;         // mm, measured
table_t = 25;         // mm  // VERIFY: only used for the picture

/* [Hidden] */
$fn = 64;
eps = 0.01;
touch = 0.05;         // tiny gap so parts that rest on each other don't count as collisions
base_h = box_h - lid_t;
cy = box_w / 2;
btn_z = box_h + touch;                          // bezel underside sits on the lid
in_y4 = box_w - wall;                           // inside face of Wall 4
in_x3 = box_l - wall;                           // inside face of Wall 3
sled_y = in_y4 - sled_t - touch;                // front face of the sled
board_under_y = sled_y - qt_gap - bff_stack_h;  // BFF underside
board_cz = board_z0 + bff_body[1] / 2;          // board centre, Z
port_x = board_cx + bff_body[0] / 2;            // USB-C face of the QT Py
post_l = sled_y - (board_under_y + bff_t);
port_y = board_under_y + usb_z;
usb_pad_t = usb_gap + usb_pad_press;
boss_c = wall + boss_d / 2 - 0.5;
boss_pts = [[boss_c, boss_c], [box_l - boss_c, boss_c], [boss_c, box_w - boss_c]];
boss_names = ["S1", "S2", "S4"];
post_xz = [for (sa = [-1, 1], sl = [-1, 1])
              [board_cx + sa * bff_holes[0] / 2, board_cz + sl * bff_holes[1] / 2]];
// Magnet pockets as [x, y, z, outward normal]: M1-M3 on Wall 1 (-X); M4-M6 on Wall 2 (-Y).
mag_depth = mag_t + mag_foam - mag_proud;      // pocket depth
// Window centres [X, Z] in model axes: W1 over CHG (H1 side, toward the lid), W2 over DON.
win_xz = [[board_cx + led_u, board_cz + led_v], [board_cx + led_u, board_cz - led_v]];
mags = [for (p = mag_w1) [0, p[0], p[1], "x"], for (p = mag_w2) [p[0], 0, p[1], "y"]];

// BFF frame -> model: across (+X, USB side) -> +X (Wall 3), along -> -Z, QT Py side -> +Y (Wall 4).
module at_board() {
    translate([board_cx, board_under_y, board_cz])
        multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]) children();
}

// Place children on a magnet spot with local +Z pointing into the box.
module at_mag(m) {
    translate([m[0], m[1], m[2]]) if (m[3] == "x") yrot(90) children(); else xrot(-90) children();
}

// ---------------- Part A: base ----------------
module base() {
    difference() {
        union() {
            difference() {
                cuboid([box_l, box_w, base_h], rounding=corner_r, edges="Z", anchor=FRONT+LEFT+BOT);
                translate([wall, wall, back_t])
                    cuboid([box_l - 2 * wall, box_w - 2 * wall, base_h], rounding=corner_r - wall / 2,
                           edges="Z", anchor=FRONT+LEFT+BOT);
            }
            for (p = boss_pts) translate([p[0], p[1], 0]) cylinder(d=boss_d, h=base_h);
            // pads inside the walls behind each magnet
            for (m = mags) at_mag(m) cylinder(d=mag_d + 4, h=mag_depth + 1.6);
            sled_guides();
            gauge_guides();
            battery_ribs();
        }
        for (p = boss_pts) translate([p[0], p[1], base_h - pilot_depth]) cylinder(d=m3_pilot, h=pilot_depth + eps);
        // magnet pockets, open to the outside
        for (m = mags) at_mag(m) down(eps) cylinder(d=mag_d + 2 * mag_clear, h=mag_depth + eps);
        // USB-C cable opening in Wall 3, in line with the QT Py port
        translate([in_x3 - eps, port_y - usb_open[1] / 2, board_cz - usb_open[0] / 2])
            cube([wall + 2 * eps, usb_open[1], usb_open[0]]);
        // groove in Wall 3 for the sled's edge (open at the lid end); also removes the rounded
        // inside corner so the cable plug and sled clear it
        g_y0 = min(sled_y - sled_clear, in_y4 - (corner_r - wall / 2) - 0.1);
        translate([in_x3 - 3, g_y0, back_t]) cube([3 + 1.2, in_y4 - g_y0 + eps, base_h]);
        // windows W1, W2: pockets in the inside of Wall 4, thin skin left outside
        if (led_windows) for (c = win_xz) translate([c[0] - window[0] / 2, in_y4 - eps, c[1] - window[1] / 2])
            cube([window[0], wall - window_t + eps, window[1]]);
    }
}

// Channel on Wall 4 that holds the sled's Wall 1 edge (the other edge sits in Wall 3).
module sled_guides() {
    gh = back_t + sled_h + 4;
    translate([sled_x0 - 2.4 - sled_clear, in_y4 - sled_t - sled_clear - 1.6, 0])
        difference() {
            cube([4.4 + sled_clear, sled_t + sled_clear + 1.6, gh]);
            translate([2.4, 1.6, -eps]) cube([2 + sled_clear + eps, sled_t + sled_clear + eps, gh + 2 * eps]);
        }
}

// Two L-shaped ribs on Wall 1; the gauge slides in between them.
module gauge_guides() {
    gh = back_t + 12;
    for (s = [0, 1]) {
        y = s == 0 ? gauge_y - 0.4 - 1.6 : gauge_y + gauge[1] + 0.4;
        translate([wall, y, 0]) cube([gauge[2] + 0.6 + 1.6, 1.6, gh]);
        translate([wall + gauge[2] + 0.6, s == 0 ? y : y - 2, 0]) cube([1.6, 3.6, gh]);
    }
}

// Two low ribs hold the battery on edge along Wall 2.
module battery_ribs() {
    y0 = batt_y + battery[2] + 0.3;
    for (x = [batt_x + 4, batt_x + battery[0] - 8])
        translate([x, y0, 0]) cube([4, 1.6, back_t + rib_h]);
}

// ---------------- Part B: lid (modelled in place; printed outer face down) ----------------
module lid_in_place() {
    in_l = box_l - 2 * wall - 2 * lip_clear;
    in_w = box_w - 2 * wall - 2 * lip_clear;
    difference() {
        union() {
            translate([0, 0, base_h])
                cuboid([box_l, box_w, lid_t], rounding=corner_r, edges="Z", anchor=FRONT+LEFT+BOT);
            translate([wall + lip_clear, wall + lip_clear, base_h - lip_h]) difference() {
                cuboid([in_l, in_w, lip_h], rounding=corner_r - wall / 2, edges="Z", anchor=FRONT+LEFT+BOT);
                translate([lip_w, lip_w, -eps])
                    cuboid([in_l - 2 * lip_w, in_w - 2 * lip_w, lip_h + 2 * eps], rounding=1, edges="Z",
                           anchor=FRONT+LEFT+BOT);
            }
        }
        for (p = boss_pts) {
            translate([p[0], p[1], base_h - lip_h - eps]) cylinder(d=m3_clear, h=lid_t + lip_h + 2 * eps);
            translate([p[0], p[1], base_h - lip_h - eps]) cylinder(d=boss_d + 2 * lip_clear, h=lip_h + eps);
        }
        translate([btn_x, cy, base_h - eps]) cylinder(d=btn_hole_d, h=lid_t + 2 * eps);
        for (s = [-1, 1]) hull()
            for (r = peg_slot_r)
                translate([btn_x + s * r * cos(btn_rot), cy + s * r * sin(btn_rot), base_h - eps])
                    cylinder(d=btn_peg_d + 2 * peg_clear, h=lid_t + 2 * eps);
    }
}

module lid() { translate([0, box_w, box_h]) xrot(180) lid_in_place(); }

// ---------------- Part D: board sled (modelled in place; printed flat, posts up) ----------------
module sled_in_place(pad=usb_pad) {
    difference() {
        union() {
            translate([sled_x0, sled_y, back_t + touch])
                cube([in_x3 + 1.2 - sled_clear - sled_x0, sled_t, sled_h]);
            for (p = post_xz) translate([p[0], sled_y + eps, p[1]]) xrot(90) cylinder(d=post_d, h=post_l);
            // USB-C pad: over the shell, stopping where the cable-plug notch starts
            if (pad) translate([port_x - usb_shell[0] + 0.3, sled_y - usb_pad_t, board_cz - usb_pad_w / 2])
                cube([usb_shell[0] - 1.3, usb_pad_t + eps, usb_pad_w]);
        }
        for (p = post_xz)
            translate([p[0], sled_y - post_l - eps, p[1]]) xrot(-90) cylinder(d=m25_pilot, h=post_l - 1);
        // light holes behind windows W1, W2, stopping short of the posts beside the LEDs
        hole_x1 = min(window[0] / 2, board_cx + bff_holes[0] / 2 - post_d / 2 - 0.4 - win_xz[0][0]);
        if (led_windows) for (c = win_xz) translate([c[0] - window[0] / 2, sled_y - eps, c[1] - window[1] / 2])
            cube([window[0] / 2 + hole_x1, sled_t + 2 * eps, window[1]]);
        // notch for the cable plug
        translate([port_x - 1, sled_y - eps, board_cz - usb_open[0] / 2])
            cube([20, sled_t + 2 * eps, usb_open[0]]);
    }
}

module sled() { translate([0, 0, sled_y + sled_t]) xrot(-90) sled_in_place(); }

// ---------------- Components, magnets and the table ----------------
module button_in_place() { translate([btn_x, cy, btn_z]) zrot(btn_rot) arcade_button(nut_z=-lid_t - 2 * touch); }
module gauge_in_place() { translate([wall + 0.3 + gauge[2], gauge_y, back_t + touch]) yrot(-90) fuel_gauge(); }
module battery_in_place() { translate([batt_x, batt_y + battery[2], back_t + touch]) xrot(90) lipo(); }
module magnets() {
    for (m = mags) at_mag(m) down(mag_proud - touch) color("dimgray") cylinder(d=mag_d, h=mag_t + mag_foam - touch);
}

module components() {
    button_in_place();
    at_board() bff_stack();
    gauge_in_place();
    battery_in_place();
}

// A charging cable plugged in through Wall 3.
module cable_plug() { translate([port_x + touch, port_y, board_cz]) xrot(90) usb_plug_dummy(); }

// Tabletop and the two aprons that form the corner (model axes; the tabletop is at -Z).
module table() {
    color("lightsteelblue", 0.35) {
        translate([-apron_t, -apron_t, -table_t]) cube([180, 180, table_t]);  // tabletop
    }
    color("slategray", 0.5) {
        translate([-apron_t, -apron_t, 0]) cube([apron_t, 180, apron_h]);    // end apron, on Wall 1
        translate([0, -apron_t, 0]) cube([180 - apron_t, apron_t, apron_h]); // side apron, on Wall 2
    }
}

// ---------------- Labels (preview only) ----------------
module tag(txt, size=6) {
    color("black") linear_extrude(0.6) text(txt, size=size, font="Liberation Sans:style=Bold",
                                             halign="center", valign="center");
}
module box_labels() {
    translate([-0.6, cy, 40]) rotate([0, -90, 0]) zrot(90) tag("WALL 1");
    translate([box_l / 2, -0.6, 40]) rotate([90, 0, 0]) tag("WALL 2");
    translate([box_l + 0.6, cy - 12, 40]) rotate([0, 90, 0]) zrot(-90) tag("WALL 3");
    translate([box_l / 2 - 14, box_w + 0.6, 40]) rotate([-90, 0, 0]) tag("WALL 4");
    if (led_windows) for (i = [0 : 1]) translate([win_xz[i][0] - 12, box_w + 0.6, win_xz[i][1]]) rotate([-90, 0, 0])
        tag(i == 0 ? "W1 CHG" : "W2 DON", 3);
    translate([box_l + 0.6, port_y - 12, board_cz]) rotate([0, 90, 0]) zrot(-90) tag("USB-C", 3.5);
    translate([board_cx, sled_y + 1, back_t + sled_h + 0.1]) tag("D", 4);
    for (i = [0 : len(mags) - 1]) {
        m = mags[i];
        at_mag(m) down(0.7) mirror([1, 0, 0]) tag(str("M", i + 1), 3);
    }
}
module lid_labels() {
    translate([box_l / 2, 4, box_h + touch]) tag("B", 4);
    for (i = [0 : len(boss_pts) - 1])
        translate([boss_pts[i][0] + (i == 1 ? -6 : 6), boss_pts[i][1] + (i < 2 ? 4 : -4),
                   box_h + touch]) tag(boss_names[i], 3.5);
}

// Everything in model axes. drop = box pulled down out of the corner (Z);
// lid_drop = lid pulled further off the box (Z).
module scene(drop=0, lid_drop=0, see_through=false) {
    a = see_through ? 0.3 : 1;
    // Opaque parts first: OpenSCAD only shows them through see-through parts drawn later.
    up(drop) {
        up(lid_drop) { button_in_place(); lid_labels(); }
        color("orange") sled_in_place();
        at_board() bff_stack();
        gauge_in_place();
        battery_in_place();
        magnets();
        box_labels();
        color("whitesmoke", a) base();
        up(lid_drop) color("lightblue", a) lid_in_place();
    }
    table();
}

// Mounted pose (left corner): top up, Wall 1 toward the player (+Y), Wall 2 on the left edge (+X).
module mounted() { zrot(-90) xrot(180) children(); }

if (part == "assembly") mounted() scene();
if (part == "xray") mounted() scene(see_through=true);
if (part == "exploded") mounted() scene(drop=45, lid_drop=40);
if (part == "base") base();
if (part == "lid") lid();
if (part == "sled") sled();
if (part == "sled_section") intersection() {  // cut through the USB-C pad, to check its reach
    union() { color("orange") sled_in_place(); at_board() bff_stack(); }
    translate([0, 0, board_cz - 50]) cube([box_l, box_w, 50]);
}
// One job with a base, lid and sled per box, each in its print orientation.
plate_boxes = 2;  // [1, 2]
if (part == "plate") {
    pg = 6;  // mm between parts
    for (i = [0 : plate_boxes - 1]) {
        translate([i * (box_l + pg), 0, 0]) base();
        translate([i * (box_l + pg), box_w + pg, 0]) lid();
        translate([plate_boxes * (box_l + pg) - sled_x0, i * (sled_h + pg), 0]) sled();
    }
}
if (part == "collisions") {
    // the USB-C pad presses on the QT Py on purpose, so leave it out here
    intersection() { union() { base(); lid_in_place(); sled_in_place(pad=false); } components(); }
    intersection() { union() { base(); lid_in_place(); sled_in_place(); } cable_plug(); }
    intersection() { union() { base(); lid_in_place(); } sled_in_place(); }
    intersection() { union() { lid_in_place(); sled_in_place(); components(); } magnets(); }
}
