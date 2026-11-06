// bff-reference.scad: the QT Py + Terminal Block BFF dummy with its mounting holes labelled,
// for measuring LED positions. Not printed.
// View it from the top: QT Py side up, USB-C edge toward you (bottom of the screen).
include <BOSL2/std.scad>
include <components.scad>

$fn = 48;
lbl_z = bff_stack_h + 1;   // labels float above the stack so the top view shows them

module tag(txt, size=3) {
    color("black") linear_extrude(0.4) text(txt, size=size, font="Liberation Sans:style=Bold",
                                             halign="center", valign="center");
}

// Rotate so the USB-C edge (+X in the board frame) points toward the viewer (-Y).
zrot(-90) bff_stack();

// Hole centres after the rotation: H1 bottom-left, H2 bottom-right, H3 top-right, H4 top-left.
holes = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
for (i = [0 : 3]) {
    x = holes[i][0] * bff_holes[1] / 2;
    y = holes[i][1] * bff_holes[0] / 2;
    color("red") translate([x, y, 0]) cylinder(d=1, h=lbl_z);   // marks the hole centre
    translate([x + holes[i][0] * 7.5, y, lbl_z]) tag(str("H", i + 1), 4);
}
translate([0, -bff_body[0] / 2 - 9, lbl_z]) tag("USB-C edge (toward you)", 3);
translate([0, bff_body[0] / 2 + 14, lbl_z]) tag("H1-H2 and H3-H4: 32.8 apart", 2.5);
translate([0, bff_body[0] / 2 + 10, lbl_z]) tag("H1-H4 and H2-H3: 25.15 apart", 2.5);
