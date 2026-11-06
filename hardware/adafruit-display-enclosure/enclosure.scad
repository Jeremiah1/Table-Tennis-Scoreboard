// enclosure.scad: wall-hung enclosure for the Adafruit 128x64 2 mm LED matrix (#6484)
// with the Matrix Portal S3 plugged into its back.
//
// Coordinates: X/Y as seen FROM THE BACK with the Portal on the left (the measuring
// convention in AGENTS.md), origin at the panel's lower-left corner. Z = 0 is the LED face,
// +Z points back toward the wall.
//
// Parts (4 big prints + optional coupon):
//   back_left / back_right  : trays that carry the panel (M4 screws), the hook pockets and
//                             the top/bottom walls. Print back face down. No supports.
//   end_left / end_right    : the side wings. Left holds the Portal window, right holds the
//                             barrel jack. Print front face down. No supports.
//   coupon                  : fit test for the M4 screw, M3 pilot, jack and sheet groove.
//   jack_coupon             : the jack area cut from back_right and end_right (2 pieces), to test
//                             the cradle with the real jack and plug.
//   left_tray_jack_coupon   : back_left and jack_coupon on one plate.
//   wings                   : end_left and end_right on one plate.
//   portal_check            : labeled drawing of the Portal window for measuring the left tray +
//                             panel with calipers (preview only, F5 in the GUI).
// The clear front sheet slides in from the top in front of the LEDs; the wing lips hide the
// outermost LED column on each side because the 10 in sheet is shorter than the panel.
include <BOSL2/std.scad>

/* [Part] */
part = "assembly"; // [assembly, exploded, hook_section, back_left, back_right, end_left, end_right, coupon, jack_coupon, left_tray_jack_coupon, wings, collisions, portal_check]

/* [LED panel] */
// Left-to-right M4 hole positions. The left tray (printed 2026-10-28) fits with its holes at 93.7 / 6.5,
// so the model's x = 0 is where that tray puts the left edge, and the left values stay. The right side is
// measured from the right edge (2026-11-02), the span across the middle hole to hole, and panel_w follows
// from them: it is the right edge as seen from the left tray (a ruler over 256 mm is not this exact).
// The right tray printed 2026-11-02 used 68.7 / 93.7 / 6.5 (edge readings by eye) and missed by ~2.5.
m4_dx_mid_l = 93.7;     // left tray as printed: left edge to the holes near the top/bottom edges
m4_dx_end_l = 6.5;      // left tray as printed: left edge to the holes near the left end
m4_span_mid = 69.6 - 3.4;      // measured 2026-11-02: the two holes near the top edge either side of the middle, inside jaws across the far sides, minus the 3.4 hole
m4_dx_mid_r = 96.5 - 3.86 / 2; // measured 2026-11-02: right end to the far side of an M4 screw (thread 3.86) in the hole near the top edge
m4_dx_end_r = 9.55 - 3.86 / 2; // measured 2026-11-02: right end to the far side of an M4 screw in the upper right-end hole
panel_w = m4_dx_mid_l + m4_span_mid + m4_dx_mid_r;   // 254.47 (was 256.1 by ruler; product page 256)
panel_h = 128.07;       // measured
panel_t = 14.6;         // measured, LED face to flat back
nub_d = 3.05;           // measured
nub_h = 3.0;            // measured
// nub centers [x, y], measured to nub edge + radius
nubs = [[63.23, panel_h - 10.43], [panel_w - 63.26, 10.38]];
// M4 threaded holes, centers [x, y]. x: see above. y from hole-to-hole spacing
// (calipers across far sides - 3.4 hole, 2026-10-29): left-end pair 60.0 apart, middle pair 107.85
// apart, centred top to bottom (edge-to-hole readings of 9.0 / 33.1 were ~1 mm off)
m4_y_mid = (panel_h - 107.85) / 2;   // 10.1
m4_y_end = (panel_h - 60.0) / 2;     // 34.0
m4_holes = [
    [m4_dx_mid_l, m4_y_mid], [m4_dx_mid_l, panel_h - m4_y_mid], [panel_w - m4_dx_mid_r, m4_y_mid], [panel_w - m4_dx_mid_r, panel_h - m4_y_mid],
    [m4_dx_end_l, m4_y_end], [m4_dx_end_l, panel_h - m4_y_end], [panel_w - m4_dx_end_r, m4_y_end], [panel_w - m4_dx_end_r, panel_h - m4_y_end]];
// 4-pin power connector (stays plugged in): center, size, height with cable
conn_c = [panel_w - 108.15, panel_h - 63.03];   // measured
conn_size = [8.5, 15.85];                         // measured
conn_h = 12;                                      // measured

/* [Matrix Portal S3] */
portal_overhang = 28;    // measured: past the panel's left edge
portal_top = 41.4;       // measured: panel top edge to board top edge
portal_size = [63.6, 44.3];  // product page
portal_z0 = 16.2;        // measured from LED face: board underside
portal_edge_z1 = 21.7;   // measured from LED face: highest part on the left edge (USB/buttons)
portal_tall = 15;        // measured: HUB75 socket height above the panel back
usb_c_y = panel_h - 79.2;    // measured (~)
portal_edge_t = 5.2;     // measured 2026-10-29: board underside to the button tops (portal_edge_z1 - portal_z0 says 5.5)
portal_play = 0.2;       // board edge between the wing's ledge and the tray's tab (it wobbles in the HUB75 socket)

/* [Barrel jack adapter #368] */
jack_y = panel_h / 2;    // where it sits along the right edge (free choice)
jack_len = 37.4;                  // measured, total: terminal end to nose tip
jack_nose_len = 11.6;             // measured: plain 10 mm cylinder
jack_step = 12.5;                 // measured: 6-7 stepped squares, each smaller, down to the nose
jack_body = [9.6, 14, 11.8];      // measured
jack_term = [jack_len - jack_nose_len - jack_step - jack_body[0], 10.15, 10.15];  // length = the rest (3.7; measured ~4), width, height measured
jack_nose_d = 10;                 // measured
jack_pad_gap = 0.25;              // body to the rest pad on the tray's back plate (cradle fit, 2026-10-28 coupon)
plug_d = 11;                      // measured: power supply plug outer diameter

/* [Enclosure] */
panel_gap = 0.4;      // clearance around the panel edge, per side
frame_wall = 3.0;     // top/bottom walls and the walls beside the panel edge
wall = 2.4;           // wing end walls and back plate
wing = 28.5;          // each wing extends this far past the panel edge (Portal + 0.5)
cavity = 16.4;        // panel back to inside of the back plate (Portal socket 15 + 1.4)
corner_r = 3;         // rounded outer corners (front view)

/* [Front sheet] */
sheet_t = 1.52;       // measured (0.060 in acrylic)
sheet_gap = 0.6;      // LED face to back of sheet
groove_clear = 0.25;  // per side in the groove
groove_depth = 1.5;   // bottom groove: how far the sheet edge sits in the wall
// The 10 in sheet is shorter than the panel, so its ends sit over the LED face: a lip on each
// wing covers the outermost LED column and holds the sheet end, and a stop behind the lip
// keeps the sheet centred.
sheet_short = 1.55;   // measured 2026-10-27: panel minus sheet length (ends flush on one side, calipers at the other)
sheet_w = panel_w - sheet_short;
sheet_h = 133.1;      // cut from the 8 in side so the top edge is flush with the frame top (y_t - g_b = 133.37)
sheet_play = 0.3;     // per end, between the sheet and the stops (measurement error, acrylic expands when warm)
hide_w = 2.2;         // lip reaches this far onto the LED face: covers column 1 (LED to ~1.75), clear of column 2 (from ~2.25) VERIFY
lip = 1.2;            // front lip in front of the groove

/* [Screws] */
m4_clear_d = 5.0;     // M4 clearance through the back boss: 4.5 slides through; 5.0 gives ±0.5 for hole-position error
m4_head_d = 9.0;      // counterbore: measured head 8.0 x 3.5 tall, + clearance (matches the ±0.5 play)
m4_floor = 3.0;       // plastic under the head; M4x12 then goes 9 mm into the panel (holes >= 10 deep)
m3_pilot_d = 3.0;     // self-tapping into PLA: button-box screw test 2026-10-22 (2.7-2.9 too tight); 2.6 failed here 2026-10-27
m3_clear_d = 3.4;
m3_head_d = 6.4;      // VERIFY: measure your M3 x 10 head
m3_head_h = 2.4;
// The trays print back face down, so each counterbore's floor prints over air. Two stepped
// bridge layers (a slot as wide as the hole, then a square) keep strands out of the screw hole,
// so it needs no cleanup (2026-11-03: the printed trays' holes were stringy and had to be cut clear).
bridge_layer = 0.2;   // = the profile's layer height

/* [Wall hooks: 3M Command J-hook] */
// The enclosure stands off the wall by the hook base's thickness. A solid catch bar at the back
// face sits in the J's nook; the J's tip rises into a slot behind the bar. To hang: hold it high,
// push it back so the hooks enter the openings below the bars, lower it. To remove: lift, pull.
hook_reach = 20;      // measured: wall to the J tip (the base's back face to the tip)
hook_t = 4.8;         // measured: J thickness
hook_rise = 17;       // measured (~): bottom of the J's nook to the tip
hook_base = [21.3, 30];  // measured: base plate width, height
hook_base_t = 4.5;    // measured (~): base plate thickness incl. adhesive strip (sets the stand-off)
hook_jw = 12;         // VERIFY: width of the J itself (dummy only)
hook_w = 36;          // pocket width: wide, so the hooks' spacing can be ~7 mm off
hook_ny = 94;         // nook height on the panel (bar underside); slot stays clear of nub 1
hook_dx = 64;         // pocket center distance from the panel's side edges
hook_clear = 0.8;     // in the J gap, between the hook base and the back face
hook_floor = 1.2;     // closes the pocket so the inside never shows

/* [Hidden] */
$fn = 48;
eps = 0.01;

// ---------- derived ----------
x_l = -wing;                     // outer left
x_r = panel_w + wing;            // outer right
x_seam = 108.05;                 // fixed: the printed left tray ends at x_seam - 0.1, 14.25 right of its middle holes
                                 // (was panel_w / 2 - 20, to split the print time between the two slots)
seam_gap = 0.4;                  // between the trays (was 0.2): margin for the measured span across the middle
y_b = -panel_gap - frame_wall;   // outer bottom
y_t = panel_h + panel_gap + frame_wall;
z_in = panel_t + cavity;         // inside of back plate
z_back = z_in + wall;            // back face (against the wall)
hook_z0 = panel_t + 0.6;         // pocket floor underside, just clear of the panel back
standoff = hook_base_t + hook_clear;               // wall to back face: bottom bumpers this tall
bar_t = hook_reach - hook_t - standoff - 0.4;      // catch bar depth: fills the J gap, 0.4 to spare
pocket_u = hook_reach - standoff + 0.6;            // back face to pocket ceiling (J tip + 0.6)
hook_y0 = hook_ny - (hook_rise + 2) - hook_t - 1;  // opening bottom: room to lift the tip over the bar
hook_y1 = hook_ny + hook_rise + 1.5;               // slot top
assert(bar_t >= 3, "hook base too thick: the catch bar would be thinner than 3 mm");
assert(pocket_u <= z_back - hook_z0 - hook_floor, "hook reaches past the pocket floor");
echo(str("hooks: stand-off ", standoff, ", bar ", bar_t, " deep, pocket ", pocket_u, " deep, lift ", hook_rise + 2));
z_sheet = -sheet_gap;            // back of sheet
z_g1 = z_sheet + groove_clear;   // groove, back side
z_g0 = z_sheet - sheet_t - groove_clear;  // groove, front side
z_front = z_g0 - lip;            // front face
in_l = -panel_gap;  in_r = panel_w + panel_gap;
in_b = -panel_gap;  in_t = panel_h + panel_gap;
side_wall = frame_wall;          // wall beside the panel edge (inside the wing)
g_l = (panel_w - sheet_w) / 2 - sheet_play;   // sheet stop, hidden behind the lip
g_b = in_b - groove_depth;
grip = hide_w - (panel_w - sheet_w) / 2;      // sheet behind each lip when centred
echo(str("sheet behind each lip: ", grip, " centred, ", grip - sheet_play, " if pushed to one side"));
wing_boss = [[x_l + wall + 4, in_b + 4.4], [x_l + wall + 4, in_t - 4.4]];
wing_boss_top = z_in - 3;        // the back gets a pad here so the M3 head can sink in
jack_cz = panel_t + jack_body[2] / 2;   // jack axis height
jack_x0 = x_r - jack_len;        // terminal end
jack_xb = jack_x0 + jack_term[0];         // body start
jack_xs = jack_xb + jack_body[0];         // step start
jack_xn = jack_xs + jack_step;            // nose start
portal_x0 = -portal_overhang;
portal_y0 = panel_h - portal_top - portal_size[1];
win_y0 = portal_y0 - 1;  win_y1 = portal_y0 + portal_size[1] + 1;
win_z0 = portal_z0 - 0.7;  win_z1 = portal_edge_z1 + 1;
// ledge under the board edge: on the printed tray the button tops rest on the tab even with the panel
// face down (2026-10-29), so the board underside sits at win_z1 + 0.2 - portal_edge_t (~17.7, not the
// 16.2 measured earlier); the ledge stops portal_play below that
portal_ledge_z = win_z1 + 0.2 - portal_edge_t - portal_play;
sheet_x0 = (in_l + in_r - sheet_w) / 2;

module box(p0, p1) { translate(p0) cube([p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]); }

// outline in front view, rounded at the four outer corners
module outline_prism(z0, z1) {
    translate([0, 0, z0]) linear_extrude(z1 - z0)
        translate([x_l, y_b]) offset(r = corner_r) offset(delta = -corner_r)
            square([x_r - x_l, y_t - y_b]);
}

// ---------- dummy components ----------
module panel_dummy() {
    color("dimgray") box([0, 0, 0], [panel_w, panel_h, panel_t]);
    color("red") for (n = nubs) translate([n[0], n[1], panel_t]) cylinder(d = nub_d, h = nub_h);
    color("red") translate([conn_c[0] - conn_size[0] / 2, conn_c[1] - conn_size[1] / 2, panel_t])
        cube([conn_size[0], conn_size[1], conn_h]);
}
module portal_dummy() {
    color("green") {
        box([portal_x0, portal_y0, portal_z0], [portal_x0 + portal_size[0], portal_y0 + portal_size[1], portal_z0 + 1.6]);
        // left-edge parts (USB-C, buttons)
        box([portal_x0, portal_y0 + 2, portal_z0 + 1.6], [portal_x0 + 8, portal_y0 + portal_size[1] - 2, portal_edge_z1]);
        // HUB75 socket block at the right end of the board
        box([portal_x0 + portal_size[0] - 26, portal_y0 + 3, panel_t], [portal_x0 + portal_size[0], portal_y0 + portal_size[1] - 3, panel_t + portal_tall]);
    }
}
module jack_dummy() {
    color("magenta") {
        translate([jack_x0, jack_y - jack_term[1] / 2, jack_cz - jack_term[2] / 2]) cube(jack_term);
        translate([jack_xb, jack_y - jack_body[1] / 2, jack_cz - jack_body[2] / 2]) cube(jack_body);
        hull() {
            translate([jack_xs, jack_y - jack_body[1] / 2, jack_cz - jack_body[2] / 2]) cube([eps, jack_body[1], jack_body[2]]);
            translate([jack_xn, jack_y, jack_cz]) rotate([0, 90, 0]) cylinder(d = jack_nose_d, h = eps);
        }
        translate([jack_xn, jack_y, jack_cz]) rotate([0, 90, 0]) cylinder(d = jack_nose_d, h = x_r - jack_xn);
    }
}
module sheet_dummy() {
    color("lightblue", 0.4) translate([sheet_x0, g_b, z_sheet - sheet_t]) cube([sheet_w, sheet_h, sheet_t]);
}
// 3M J-hook, hung: the bar rests in the nook and leans on the J (the display tips forward)
module hook_dummy(x) {
    zw = z_back - bar_t + hook_reach - hook_t;   // the wall
    color("white") {
        box([x - hook_base[0] / 2, hook_ny - 8, zw - hook_base_t], [x + hook_base[0] / 2, hook_ny - 8 + hook_base[1], zw]);
        box([x - hook_jw / 2, hook_ny - hook_t, zw - hook_reach], [x + hook_jw / 2, hook_ny, zw - hook_base_t]);
        box([x - hook_jw / 2, hook_ny - hook_t, zw - hook_reach], [x + hook_jw / 2, hook_ny + hook_rise, zw - hook_reach + hook_t]);
    }
}
module dummies() { panel_dummy(); portal_dummy(); jack_dummy(); sheet_dummy(); hook_dummy(hook_dx); hook_dummy(panel_w - hook_dx); }

// ---------- back trays ----------
module back_tray(side) {   // side = 0 left, 1 right
    xa = side == 0 ? x_l : x_seam - 0.1 + seam_gap;
    xb = side == 0 ? x_seam - 0.1 : x_r;
    wl = side == 0 ? in_l : x_seam - 0.1 + seam_gap;     // top/bottom walls span (wings own the corners)
    wr = side == 0 ? x_seam - 0.1 : in_r;
    holes = [for (h = m4_holes) if ((h[0] < x_seam) == (side == 0)) h];
    hook_x = side == 0 ? hook_dx : panel_w - hook_dx;
    wb = side == 0 ? wing_boss : [for (b = wing_boss) [panel_w - b[0], b[1]]];
    difference() {
        union() {
            intersection() {
                outline_prism(z_in, z_back);
                box([xa, y_b - 1, z_in], [xb, y_t + 1, z_back]);
            }
            // bottom wall (with groove) and top wall (stops behind the sheet)
            box([wl, y_b, z_front], [wr, in_b, z_in + eps]);
            box([wl, in_t, z_g1], [wr, y_t, z_in + eps]);
            // M4 bosses down to the panel back
            for (h = holes) translate([h[0], h[1], panel_t + 0.02]) cylinder(d = 12, h = z_in - panel_t + eps);
            // pads over the wing bosses, trimmed 0.2 clear of the wing's end wall and top/bottom walls
            // (2026-11-02: the full Ø9 pads reached 0.5 into the end wall; the printed left tray still has them)
            for (b = wb) intersection() {
                translate([b[0], b[1], wing_boss_top]) cylinder(d = 9, h = z_in - wing_boss_top + eps);
                box([x_l + wall + 0.2, in_b + 0.2, wing_boss_top - 1], [x_r - wall - 0.2, in_t - 0.2, z_in + 1]);
            }
            // hook pocket: closed box, only as deep as the hook needs
            box([hook_x - hook_w / 2 - 1.6, hook_y0 - 1.6, z_back - pocket_u - hook_floor], [hook_x + hook_w / 2 + 1.6, hook_y1 + 1.6, z_back - eps]);
            if (side == 0) {
                // tab that closes the Portal window above the board
                box([x_l + 0.2, win_y0 + 0.2, win_z1 + 0.2], [x_l + wall - 0.2, win_y1 - 0.2, z_in + eps]);
            } else {
                jack_holder_back();
            }
        }
        // bottom groove
        box([wl - eps, g_b, z_g0], [wr + eps, in_b + eps, z_g1]);
        for (h = holes) translate([h[0], h[1], 0])
            bridged_cbore(m4_clear_d, m4_head_d, panel_t - eps, panel_t + m4_floor);
        for (b = wb) translate([b[0], b[1], 0])
            bridged_cbore(m3_clear_d, m3_head_d, wing_boss_top - eps, z_back - m3_head_h);
        // hook pocket: opening below the catch bar, slot for the J tip behind it
        box([hook_x - hook_w / 2, hook_y0, z_back - pocket_u], [hook_x + hook_w / 2, hook_ny, z_back + 1]);
        box([hook_x - hook_w / 2, hook_ny - eps, z_back - pocket_u], [hook_x + hook_w / 2, hook_y1, z_back - bar_t]);
    }
}

// Screw hole + counterbore for a part printed with the counterbore toward the bed (+Z down on the
// plate). z0 = hole start, zf = counterbore floor. The first layer over the counterbore leaves a
// slot hole_d wide (its bridges run along the slot, anchored on the counterbore wall), the second
// a hole_d square (bridges across the slot), then the round hole. All are >= the round hole.
module bridged_cbore(hole_d, head_d, z0, zf) {
    translate([0, 0, z0]) cylinder(d = hole_d, h = zf - z0 - 2 * bridge_layer + eps);
    translate([-hole_d / 2, -hole_d / 2, zf - 2 * bridge_layer]) cube([hole_d, hole_d, bridge_layer + eps]);
    translate([-hole_d / 2, -head_d / 2 - eps, zf - bridge_layer]) cube([hole_d, head_d + 2 * eps, bridge_layer + eps]);
    translate([0, 0, zf]) cylinder(d = head_d, h = 50);
}
echo(str("counterbore floors from the bed (want multiples of ", bridge_layer, "): M4 ", z_back - panel_t - m4_floor, ", M3 ", m3_head_h));

// right tray: cradle walls, pull-out shoulder, push-in stops, and the tongue in the end-wall slot
module jack_holder_back() {
    zb = panel_t + 0.3;
    // rest pad on the back plate: the body (front face on the panel back and the wing's inner wall)
    // is held from behind too, instead of a 4.6 mm gap (2026-11-03: the jack looked loose in the tray)
    translate([jack_xb, jack_y - jack_body[1] / 2 - 0.25, panel_t + jack_body[2] + jack_pad_gap])
        cube([jack_body[0], jack_body[1] + 0.5, z_in - panel_t - jack_body[2] - jack_pad_gap + eps]);
    difference() {
        union() {
            // side walls along the body
            for (s = [-1, 1]) translate([jack_xb, jack_y + s * (jack_body[1] / 2 + 0.25) + (s < 0 ? -2 : 0), zb])
                cube([jack_xs - jack_xb, 2, z_in - zb + eps]);
            // shoulder wall: the step bears on it when the plug is pulled out
            translate([jack_xn + 0.2, jack_y - jack_body[1] / 2 - 2.25, zb]) cube([2.4, jack_body[1] + 4.5, z_in - zb + eps]);
            // push-in stops behind the body, either side of the terminal block
            for (s = [-1, 1]) translate([jack_xb - 2.6, jack_y + s * (jack_term[1] / 2 + 0.4) + (s < 0 ? -2.4 : 0), zb])
                cube([2.4, 2.4, z_in - zb + eps]);
            // tongue that fills the end-wall slot above the nose
            translate([x_r - wall + 0.2, jack_y - jack_nose_d / 2 + 0.05, jack_cz]) cube([wall - 0.4, jack_nose_d - 0.1, z_in - jack_cz + eps]);
        }
        translate([jack_x0 - 5, jack_y, jack_cz]) rotate([0, 90, 0]) cylinder(d = jack_nose_d + 0.4, h = 60);
        // body clearance
        translate([jack_xb - 0.2, jack_y - jack_body[1] / 2 - 0.25, zb - eps]) cube([jack_body[0] + jack_step + 0.3, jack_body[1] + 0.5, jack_body[2] + 0.4]);
        // shoulder wall is open toward the front so the jack drops in
        translate([jack_xn, jack_y - jack_nose_d / 2 - 0.2, zb - eps]) cube([10, jack_nose_d + 0.4, jack_cz - zb]);
    }
}

// ---------- wings ----------
module wing_end(side) {
    // built as the left wing, mirrored for the right
    xi = in_l;   // inner face of the frame wall beside the panel
    difference() {
        union() {
            intersection() {
                outline_prism(z_front, z_in);
                difference() {
                    box([x_l, y_b, z_front], [xi, y_t, z_in]);
                    // hollow interior
                    box([x_l + wall, in_b, z_front + 2], [xi - side_wall, in_t, z_in + 1]);
                    // behind the panel the wing opens into the main cavity
                    box([xi - side_wall - eps, in_b, panel_t], [xi + eps, in_t, z_in + 1]);
                }
            }
            for (b = wing_boss) translate([b[0], b[1], z_front]) cylinder(d = 8, h = wing_boss_top - z_front);
            // lip over the outermost LED column, and the sheet stop behind it (both clear of the LED face)
            box([xi - eps, in_b, z_front], [hide_w, y_t, z_g0]);
            box([xi - eps, in_b, z_g0 - eps], [g_l, y_t, z_g1]);
        }
        for (b = wing_boss) translate([b[0], b[1], wing_boss_top - 12]) cylinder(d = m3_pilot_d, h = 13);
        if (side == 0) {
            // Portal window, open to the back (the tray's tab closes the top)
            difference() {
                box([x_l - 1, win_y0, win_z0], [x_l + wall + 1, win_y1, z_in + 1]);
                // ledge the board edge rests on; the outer face stays open below the board for a USB-C plug
                box([portal_x0, win_y0 - 1, win_z0 - 1], [x_l + wall + 2, win_y1 + 1, portal_ledge_z]);
            }
        }
    }
}

// right wing: saddle under the nose, beyond the tray's shoulder wall
module jack_saddle() {
    difference() {
        box([jack_xn + 3, jack_y - jack_body[1] / 2, z_front + 1], [x_r - wall + eps, jack_y + jack_body[1] / 2, jack_cz]);
        translate([jack_xn, jack_y, jack_cz]) rotate([0, 90, 0]) cylinder(d = jack_nose_d + 0.4, h = 60);
    }
}

module wing_part(side) {
    if (side == 0) wing_end(0);
    else translate([panel_w, 0, 0]) mirror([1, 0, 0]) wing_end(1);
}

// the end-wall slot for the jack nose (cut after mirroring)
module jack_slot() {
    translate([x_r - wall - 1, jack_y, jack_cz]) rotate([0, 90, 0]) cylinder(d = jack_nose_d + 0.4, h = wall + 2);
    translate([x_r - wall - 1, jack_y - (jack_nose_d + 0.4) / 2, jack_cz]) cube([wall + 2, jack_nose_d + 0.4, z_in]);
}

module end_right_asm() { difference() { union() { wing_part(1); jack_saddle(); } jack_slot(); } }

// ---------- fit-test coupon ----------
// 1: M4 counterbore with the real 3 mm floor: screw it into a panel hole (M4 x 12 should grip ~9 mm)
// 2: M3 pilot boss: drive an M3 x 10 in
// 3: jack nose slot, as in the right end wall: drop the nose in
// 4: upright sheet slots at +0.25 / +0.4 / +0.55 mm per side (1 / 2 / 3 notches): drop a scrap of the acrylic in
module coupon() {
    base = 2;
    slot_h = 8;
    difference() {
        union() {
            cube([84, 22, base]);
            translate([11, 11, 0]) cylinder(d = 14, h = base + m4_floor + 4);
            translate([28, 11, 0]) cylinder(d = 8, h = 12);
            translate([36, 0, 0]) cube([wall, 22, 7 + jack_nose_d]);
            translate([46, 0, 0]) cube([38, 22, base + slot_h]);
        }
        translate([11, 11, -eps]) cylinder(d = m4_clear_d, h = 30);
        translate([11, 11, m4_floor]) cylinder(d = m4_head_d, h = 30);
        translate([28, 11, 2]) cylinder(d = m3_pilot_d, h = 20);
        translate([36 - 1, 11, 7 + jack_nose_d / 2]) rotate([0, 90, 0]) cylinder(d = jack_nose_d + 0.4, h = wall + 2);
        translate([36 - 1, 11 - (jack_nose_d + 0.4) / 2, 7 + jack_nose_d / 2]) cube([wall + 2, jack_nose_d + 0.4, 20]);
        // slots run through front to back, so any scrap width fits; notches on the top count the slot
        for (i = [0 : 2]) {
            gw = sheet_t + 2 * (0.25 + 0.15 * i);
            x0 = 46 + 6 + i * 12;
            translate([x0, -eps, base]) cube([gw, 22 + 2 * eps, slot_h + 1]);
            for (k = [0 : i]) translate([x0 - 2.3 - k * 1.6, -eps, base + slot_h - 1]) cube([0.8, 3, 2]);
        }
    }
}

// ---------- jack fit-test coupon ----------
// The jack area cut straight from the right tray and the right wing, laid out for printing.
// Hold the two together (the tray's tongue drops into the end-wall slot), with a finger in place of the panel.
jc_y0 = jack_y - 13;  jc_y1 = jack_y + 13;
jc_x0 = jack_x0 - 4;
module jack_coupon() {
    // tray piece, back face down
    translate([-jc_x0, jc_y1, z_back]) rotate([180, 0, 0])
        intersection() { back_tray(1); box([jc_x0, jc_y0, panel_t], [x_r + 1, jc_y1, z_back + 1]); }
    // wing piece, front face down
    translate([-in_r, -jc_y0 + (jc_y1 - jc_y0) + 8, -z_front])
        intersection() { end_right_asm(); box([in_r, jc_y0, z_front - 1], [x_r + 1, jc_y1, z_in]); }
}

// ---------- assembly and print layouts ----------
module back_print(side) {
    translate([0, 0, z_back]) rotate([180, 0, 0]) translate([side == 0 ? -x_l : -x_seam, 0, 0]) back_tray(side);
}

if (part == "assembly") {
    color("whitesmoke") back_tray(0);
    color("gainsboro") back_tray(1);
    color("silver") wing_part(0);
    color("silver") end_right_asm();
    dummies();
}
// pulled apart along the assembly order: trays, panel + Portal + jack, wings, sheet
if (part == "exploded") {
    color("whitesmoke") translate([-20, 0, 60]) back_tray(0);
    color("gainsboro") translate([20, 0, 60]) back_tray(1);
    panel_dummy(); portal_dummy(); jack_dummy();
    color("silver") translate([-60, 0, -40]) wing_part(0);
    color("silver") translate([60, 0, -40]) end_right_asm();
    translate([0, 0, -80]) sheet_dummy();
}
if (part == "coupon") coupon();
if (part == "jack_coupon") jack_coupon();
if (part == "left_tray_jack_coupon") { back_print(0); translate([x_seam - x_l + 10, -y_t, 0]) jack_coupon(); }
if (part == "back_left") back_print(0);
if (part == "back_right") back_print(1);
if (part == "end_left") translate([-x_l, -y_b, -z_front]) wing_part(0);
if (part == "end_right") translate([-in_r, -y_b, -z_front]) end_right_asm();
if (part == "wings") { translate([-x_l, -y_b, -z_front]) wing_part(0); translate([-x_l + hide_w + 10 + panel_gap + hide_w - in_r, -y_b, -z_front]) end_right_asm(); }
// cut through the left hook pocket, seen from the side
if (part == "hook_section") {
    intersection() {
        union() {
            color("whitesmoke") back_tray(0);
            color("silver") wing_part(0);
            dummies();
        }
        translate([x_l - 1, y_b - 1, z_front - 1]) cube([hook_dx - x_l + 1, y_t - y_b + 2, z_back + standoff - z_front + 2]);
    }
}
if (part == "collisions") {
    intersection() { union() { back_tray(0); back_tray(1); wing_part(0); end_right_asm(); } dummies(); }
}

// ---------- measuring drawing: the Portal window (preview only) ----------
// Flat 2D drawing, view from the top in the GUI. Top: section through the middle of the Portal edge
// (3x). Bottom: section through the left end wall, seen from outside (1.5x). Panel face down on the
// table: LED face = 0, up = toward the wall.
check_ys = portal_y0 + portal_size[1] / 2;
check_xs = x_l + 1.2;                                   // through the wing end wall and the tab
tab_z0 = win_z1 + 0.2;                                  // underside of the tray's tab
module sec_y() multmatrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, check_ys]]) children();   // drawing (x, z)
module sec_x() multmatrix([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, check_xs]]) children();  // drawing (-y, z)
module flat(col, h = 0) color(col) translate([0, 0, h]) linear_extrude(0.1) children();
module note(x, y, s, size = 1, col = "black", ha = "left")
    flat(col, 0.4) translate([x, y]) text(s, size = size, halign = ha, valign = "center");
module line(p0, p1, col, w = 0.12) flat(col, 0.3) hull() { translate(p0) circle(d = w, $fn = 8); translate(p1) circle(d = w, $fn = 8); }
module dim(p0, p1, col) {   // dimension line with end ticks
    v = (p1 - p0) / norm(p1 - p0);  n = [-v[1], v[0]] * 0.7;
    line(p0, p1, col);  line(p0 - n, p0 + n, col);  line(p1 - n, p1 + n, col);
}
module check_section() {
    module cut() projection(cut = true) sec_y() intersection() { children(); box([x_l - 1, check_ys - 1, -1], [8, check_ys + 1, z_back + 1]); }
    flat("lightskyblue") cut() wing_part(0);
    flat("white", 0.1) cut() back_tray(0);
    flat("dimgray", 0.1) cut() box([0, 0, 0], [panel_w, panel_h, panel_t]);
    flat("green", 0.2) cut() portal_dummy();
    color("black") translate([x_l - 1, -0.06, 0]) cube([x_l * -1 + 9, 0.12, 0.3]);
    note(-36, 37, "1. SECTION through the middle of the Portal edge (3x)", 1.3);
    note(-36, 35.2, "panel face down on the table; board resting toward the panel", 0.8, "dimgray");
    note(7.5, 32.2, "tray back plate", 0.8, "black", "right");
    note(-25.4, 27, "tab (on the tray)", 0.8);
    note(-19.5, 19.2, "USB-C / buttons", 0.8);
    note(-10, 17, "Portal board", 0.7, "white");
    note(7.5, 7, "panel", 0.9, "white", "right");
    note(-25.4, 9, "wing (blue): printing today,", 0.75, "steelblue");
    note(-25.4, 7.9, "not on the tray yet", 0.75, "steelblue");
    note(-36, 1, "table = LED face", 0.8, "dimgray");
    // A: board edge thickness, B: gap to the tab, C: overall height, D: board edge behind the tab face
    dim([-31, portal_z0], [-31, portal_edge_z1], "red");
    note(-32, (portal_z0 + portal_edge_z1) / 2, str("A ", portal_edge_t), 1.1, "red", "right");
    dim([-31, portal_edge_z1], [-31, tab_z0], "blue");
    note(-32, tab_z0 + 0.5, str("B ", tab_z0 - portal_edge_z1), 1.1, "blue", "right");
    dim([9.5, 0], [9.5, z_back], "purple");
    note(10.3, z_back / 2, str("C ", z_back), 1.1, "purple");
    line([x_l + 0.2, 11], [x_l + 0.2, tab_z0], "darkorange", 0.08);
    line([portal_x0, 11], [portal_x0, portal_z0], "darkorange", 0.08);
    dim([x_l + 0.2, 12], [portal_x0, 12], "darkorange");
    note(x_l - 0.6, 12, str("D ", portal_x0 - (x_l + 0.2)), 1.1, "darkorange", "right");
    // the wing's ledge
    flat("steelblue", 0.45) translate([portal_x0, portal_ledge_z - 0.25]) square([x_l + wall - portal_x0, 0.25]);
    line([x_l + wall, portal_ledge_z - 0.1], [x_l + wall + 2, 14.2], "steelblue", 0.08);
    note(x_l + wall + 2.2, 14, str("wing ledge (top at ", portal_ledge_z, "): lifts the board ", portal_ledge_z - portal_z0, ","), 0.7, "steelblue");
    note(x_l + wall + 2.2, 13, str("so it sits between ledge and tab with ", portal_play, " play"), 0.7, "steelblue");
}
module check_end() {
    module cut() projection(cut = true) sec_x() intersection() { children(); box([check_xs - 1, y_b - 1, -1], [check_xs + 1, y_t + 1, z_back + 1]); }
    flat("lightskyblue") cut() wing_part(0);
    flat("white", 0.1) cut() back_tray(0);
    flat("green", 0.2) cut() portal_dummy();
    color("black") translate([-y_t, -0.06, 0]) cube([y_t - y_b, 0.12, 0.3]);
    note(-y_t, 47, "2. SECTION through the left end wall, seen from outside (1.5x)", 2.6);
    note(-y_t, -3, "panel top edge", 1.8, "dimgray");
    note(-y_b, -3, "panel bottom edge", 1.8, "dimgray", "right");
    note(-y_t, 35, "tray back plate", 1.6);
    note(-y_t + 2, 8, "wing end wall", 1.6, "steelblue");
    note(-(win_y1 - 0.2) + 1, 28.8, "tab", 1.6);
    note(-check_ys, 19.5, "Portal edge", 1.6, "white", "center");
    // E / F: the tab overhangs each end of the board edge
    ya = -(portal_y0 + portal_size[1]);  yb = -portal_y0;  ta = -(win_y1 - 0.2);  tb = -(win_y0 + 0.2);
    for (x = [ta, tb]) line([x, tab_z0], [x, 27], "darkgreen", 0.15);
    for (x = [ya, yb]) line([x, portal_edge_z1], [x, 27], "darkgreen", 0.15);
    dim([ta, 26], [ya, 26], "darkgreen");
    note(ta - 1, 26, str("E ", round((ya - ta) * 10) / 10), 2, "darkgreen", "right");
    dim([yb, 26], [tb, 26], "darkgreen");
    note(tb + 1, 26, str("F ", round((tb - yb) * 10) / 10), 2, "darkgreen");
    dim([ta, 41], [tb, 41], "black");
    note(-check_ys, 43, str("G: tab length ", tb - ta), 1.8, "black", "center");
    dim([ya, 12.5], [yb, 12.5], "red");
    note(-check_ys, 10.5, str("H: board edge ", portal_size[1]), 1.6, "red", "center");
}
if (part == "portal_check") {
    scale(3) check_section();
    translate([150, -95, 0]) scale(1.5) check_end();
}
