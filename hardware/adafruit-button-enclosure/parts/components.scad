// components.scad: dummy models of the real parts, for fit and collision checks (not printed).
// Each module is drawn in its own frame; button-box.scad places them.
include <BOSL2/std.scad>

// ---- Arcade button (Adafruit 1192). Origin: button axis, at the underside of the bezel.
btn_bezel_d = 60.8;      // drawing
btn_bezel_h = 4.4;       // drawing
btn_cap_d = 51.9;        // drawing
btn_above = 14.8;        // measured: bezel underside to cap top, not pressed
btn_thread_d = 23.7;     // measured 23.5-23.7
btn_thread_l = 29.95;    // measured
btn_nut_d = 32.35;       // measured
btn_nut_t = 8.73;        // measured
btn_depth = 54.3;        // measured: bezel underside to the bottom of the switch
btn_switch = [27.7, 12.05];  // measured: length (PEG A to PEG B, X) and width (SIDE L to R, Y)
btn_switch_gap = 2;      // measured: gap between the end of the threads and the switch body
btn_peg_d = 3.43;        // measured: (41.2 outside - 34.35 inside) / 2
btn_peg_h = 2;           // VERIFY
btn_peg_r = 18.89;       // measured: (41.2 + 34.35) / 4
btn_conn_reach = 27.7 / 2 + 23;  // measured: tab + connector stick out 23 past the switch (PEG A, +X)
btn_bend = 4;            // room kept free past the connector so the wire can bend
btn_conn = [8, 12];      // VERIFY: connector width (Y) and height (Z)
btn_conn_z = -40;        // VERIFY: connector centre height below the bezel underside

module arcade_button(nut_z=-3) {
    color("red") {
        cylinder(d=btn_bezel_d, h=btn_bezel_h);
        up(btn_bezel_h) cylinder(d=btn_cap_d, h=btn_above - btn_bezel_h);
        for (s = [-1, 1]) translate([s * btn_peg_r, 0, -btn_peg_h]) cylinder(d=btn_peg_d, h=btn_peg_h);
        down(btn_thread_l) cylinder(d=btn_thread_d, h=btn_thread_l);
        translate([-btn_switch[0] / 2, -btn_switch[1] / 2, -btn_depth])
            cube([btn_switch[0], btn_switch[1], btn_depth - btn_thread_l - btn_switch_gap]);
    }
    color("darkred") translate([0, 0, nut_z - btn_nut_t]) cylinder(d=btn_nut_d, h=btn_nut_t);
    // Quick-connect on the switch tab, pointing +X (under one peg), plus room for the wire to bend.
    color("gold") translate([btn_switch[0] / 2, -btn_conn[0] / 2, btn_conn_z - btn_conn[1] / 2])
        cube([btn_conn_reach - btn_switch[0] / 2 + btn_bend, btn_conn[0], btn_conn[1]]);
}

// ---- QT Py ESP32-S3 on the Terminal Block BFF (6495).
// Origin: centre of the BFF body, on its underside. X = across the board (21), Y = along (43.25),
// +Z = the side the QT Py is on. The USB-C port is on the +X long edge.
bff_body = [21, 43.25];      // measured, straight edges
bff_t = 1.6;                 // VERIFY
bff_holes = [25.15, 32.8];   // measured 2026-10-22 over screw shanks: hole centres across (X) and along (Y)
bff_tab_d = 5.2;             // (30.35 measured across the circles) - 25.15 between centres
bff_pins = 2.5;              // measured: pins below the board
bff_stack_h = 15.5;          // measured: BFF underside to QT Py top
qtpy = [21.8, 17.8];         // QT Py board, long side across the BFF (published)
usb_z = 13.39;               // measured: USB-C shell 11.7-15.08 above the BFF underside
usb_top = 15.08;             // measured: top of the USB-C shell above the BFF underside
usb_shell = [7.3, 8.9];      // USB-C shell depth (from the port face) x width  // VERIFY

module bff_stack() {
    color("green") difference() {
        union() {
            translate([-bff_body[0] / 2, -bff_body[1] / 2, 0]) cube([bff_body[0], bff_body[1], bff_t]);
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * bff_holes[0] / 2, sy * bff_holes[1] / 2, 0]) cylinder(d=bff_tab_d, h=bff_t);
        }
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * bff_holes[0] / 2, sy * bff_holes[1] / 2, -1]) cylinder(d=2.5, h=bff_t + 2);
    }
    // Underside pins (one block per terminal row).
    color("silver") for (sy = [-1, 1])
        translate([-8, sy * (bff_body[1] / 2 - 4) - 2, -bff_pins]) cube([16, 4, bff_pins]);
    // Terminal blocks along both short ends.
    color("darkgreen") for (sy = [-1, 1])
        translate([-9, sy * (bff_body[1] / 2 - 4) - 4, bff_t]) cube([18, 8, 8.5]);
    // QT Py on its socket, USB-C flush with the +X edge.
    color("purple") translate([bff_body[0] / 2 - qtpy[0], -qtpy[1] / 2, bff_stack_h - 5])
        cube([qtpy[0], qtpy[1], 5]);
}

// ---- MAX17048 fuel gauge (5580). Origin: corner, on its underside.
gauge = [20.3, 25.7, 7.2];   // published  // VERIFY
module fuel_gauge() { color("magenta") cube(gauge); }

// ---- 500 mAh LiPo. Origin: corner. Lying flat it is 37.2 x 30.25 x 4.8.
battery = [37.2, 30.25, 4.8];  // measured
module lipo() { color("silver") cube(battery); }

// ---- A USB-C cable plug. Origin: plug face at the port, pointing +X out of the port.
usb_plug = [22, 12.5, 7];  // VERIFY: metal tip + overmold length, overmold width and height
module usb_plug_dummy() {
    color("dimgray") translate([0, -usb_plug[1] / 2, -usb_plug[2] / 2]) cube(usb_plug);
}
