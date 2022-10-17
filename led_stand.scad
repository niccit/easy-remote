// SPDX-License-Identifier: MIT

use <lib/threads.scad>
include <lib/JointSCAD.scad>

$fa = 1;
$fs = 0.4;

// base
l_length = 256;
l_width = 6;
l_height = 128;

// keyboard tray
kb_length = 55;
kb_width = 30;
kb_height = 3;

// Mortise Joint, base
m_dimensions = [20, 6, l_height / 2];
m_proportions = [0.8, 0.2, 0.8];

// Tenon Joint, base
t_dimensions = [20, 6, l_height / 2 - 5];
t_proportions = [0.7, 0.2, 0.8];

base_right_side();
translate([l_height / 2 - 22.5, -l_width + 3, -10])
	design_right();
translate([l_length / 2 - 0.001, 0, 0])
	base_left_side();
translate([(l_height / 2 + 22.5) , -l_width + 3 , -10])
	design_left();

module design_right() {
	rotate([270,180,180])
	scale([.2, .2, .02])
		surface(file = "images/adafruit_logo_right.png", center=true, invert=false);
}

module design_left() {
	rotate([270,180,180])
		scale([.2, .2, .02])
			surface(file = "images/adafruit_logo_left.png", center=true, invert=false);
}

module mounting_holes() {
	cylinder(r=2.5, h=l_width, center=true);
}

module base_right_side() {
	difference() {
	cube([l_length / 2, l_width,  l_height + 3], center=true);
		rotate([0,90,90])
		  translate([-(l_height / 2 - l_width - 0.5), (l_length / 4 - 9), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([(l_height / 2 - l_width - 4.5), (l_length / 4 - 9), 0])
			mounting_holes();
    // Mortise location
 		translate([l_length / 2 / 2 - 20, -3, -l_height / 2 / 2])
			cube([20,6,l_height / 2]);
	}
 	translate([l_length / 2 / 2 - 20, -3, -l_height / 2 / 2])
		mortise(m_dimensions, m_proportions);

  translate([0,0,-l_height / 2 - 12 - 0.001])
    keyboard_tray_right();
}

module base_left_side() {
	difference() {
   	cube([l_length / 2, l_width,  l_height + 3], center=true);
  	rotate([0,90,90])
  	translate([-(l_height / 2 - l_width - 0.5), -(l_length / 4 - 9), 0])
  		mounting_holes();
  	rotate([0,90,90])
  	translate([(l_height / 2 - l_width - 4.5), -(l_length / 4 - 9), 0])
  		mounting_holes();
	}
 	translate([-l_length / 2 / 2 - 20 - 0.001, -3, -l_height / 2 / 2 + 2])
		tenon(t_dimensions, t_proportions);

  translate([0,0,-l_height / 2 - 12 - 0.001])
    keyboard_tray_left();
}

module keyboard_tray_right() {
	cube([l_length /2, l_width, 21], center=true);
	translate([36.5, 35 - 0.001, -9])
		cube([kb_length, (kb_width * 2) + 5, kb_height], center=true);
	translate([kb_length /2 - 12.5, kb_width / 2 + 40 , -4.5 - 0.001])
		difference() {
			cylinder(r=3.5, h=6, center=true);
				ScrewHole(outer_diam=4, height=5);
		}
	translate([kb_length / 2  + 18, kb_width / 2 + 48, -6 - 0.001])
		cylinder(r=2, h=3, center=true);
	translate([kb_length / 2 + 18, kb_width / 2 + 32, -6 - 0.001])
		cylinder(r=2, h=3, center=true);
}

module keyboard_tray_left() {
	cube([l_length /2, l_width, 21], center=true);
	translate([-37, 35 - 0.001, -9])
		cube([kb_length, (kb_width * 2) + 5, kb_height], center=true);
	translate([-kb_length /2 + 12.5, kb_width / 2 + 40 , -4.5 - 0.001])
	difference() {
		cylinder(r=3.5, h=6, center=true);
			ScrewHole(outer_diam=4, height=5);
	}
	translate([-kb_length / 2 - 18, kb_width / 2 + 48, -6 - 0.001])
		cylinder(r=2, h=3, center=true);
	translate([-kb_length / 2 - 18, kb_width / 2 + 32, -6 - 0.001])
		cylinder(r=2, h=3, center=true);
}
