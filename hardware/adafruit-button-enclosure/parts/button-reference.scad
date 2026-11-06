// button-reference.scad: the arcade button dummy seen from below (switch end up), with its
// sides named, for measuring the switch. Not printed.
// Hold the real button the same way: cap down, switch pointing at you, the peg above the
// quick-connect tab at the top of the view.
include <BOSL2/std.scad>
include <components.scad>

$fn = 64;
lbl_z = btn_depth + 2;   // labels float above the switch end

module tag(txt, size=3) {
    color("black") linear_extrude(0.4) text(txt, size=size, font="Liberation Sans:style=Bold",
                                             halign="center", valign="center");
}

// Flip so the switch points up, and turn so the connector (+X) points to the top of the view.
zrot(90) xrot(180) arcade_button(nut_z=-3);

r = btn_bezel_d / 2 + 6;
translate([0, r, lbl_z]) tag("PEG A side (quick-connect tab)", 3);
translate([0, -r, lbl_z]) tag("PEG B side", 3);
translate([-r - 6, 0, lbl_z]) tag("SIDE L", 3);
translate([r + 6, 0, lbl_z]) tag("SIDE R", 3);
