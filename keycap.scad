// SPDX-License-Identifier: MIT
//
// A round keycap for Cherry MX keyboard
// Can be blank or have a raised letter added
//

$fa = 1;
$fs = 0.4;

difference() {
	// outer cylinder
	outer_cylinder();
	// inner cylinder
	translate([0, 0, 1])
		cylinder(r=8, h=7, center=true);
}

translate([0, 0, 0.25 - 0.001])
	key_lock();

//
// Show a letter on your key
// Use 0 for a blank key
//
translate([0.5, 0, 0])
	show_text(0);

//
// Modules
//

module outer_cylinder() {
	difference() {
		cylinder(r=9, h=8, center=true);
			rotate([0,180,0])
			translate([0, 0, 26])
				sphere(r=23);
	}
}

module key_lock () {
	difference() {
		cylinder(r=2.5, h=6, center=true);
		translate([0,0,1])
			cube([1, 4, 5], center=true);
		translate([0,0,1])
			cube([4, 1, 5], center=true);
	}
}

module show_text (num) {
	rotate([180,0,0])
	if (num==1)
		translate([-4.5, -3.5, 3])
			linear_extrude(height = 1)
				text("N", font = "Liberation Sans:style=Bold", size= 8);
	else if (num==2)
		translate([-4, -3.5, 3])
			linear_extrude(height = 1)
				text("P", font = "Liberation Sans:style=Bold", size=8);
	else if (num==3)
		translate([-4.5, -3.5, 3])
			linear_extrude(height = 1)
				text("H", font = "Liberation Sans:style=Bold", size=8);
	else if (num==4)
		rotate([0, 0, 180])
		translate([-5, -2.5, 3])
			linear_extrude(height = 1)
				text("Off", font = "Liberation Sans:style=Bold", size=5);
}
