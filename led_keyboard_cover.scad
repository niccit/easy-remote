// SPDX-License-Identifier: MIT

use <lib/threads.scad>
include <lib/JointSCAD.scad>

$fa = 1;
$fs = 0.4;

// keyboard tray
kb_length = 109;
kb_width = 22;
kb_height = 4;

keyboard_cover_top(4, 19) key_holes();
// translate([0, kb_width / 2 - 0.001, -4.5])
//   keyboard_cover_front();
// translate([-kb_length / 2  + 0.5 - 0.001, 0, -4])
//     keyboard_cover_side(height=6);
// translate([kb_length / 2  - 0.5 - 0.001, 0, -4.5])
//   keyboard_cover_side(height=11);

module keyboard_cover_top(num, space) {
  difference() {
    cube([kb_length, kb_width, kb_height], center=true);
		for (i = [0 : num - 1])
			translate([-kb_length / 2 / 2 + 1 + space*i, 0, 0])
				children(0);
    translate([kb_length / 2 - 6,  kb_width / 2  - 12, 1])
  	 cylinder(r=3.5, h=6, center=true);
    translate([-(kb_length / 2 - 6),  kb_width / 2  - 12, 1])
  	 cylinder(r=3.5, h=6, center=true);
	}
}

module key_holes(){
  cube([15, 16, 5], center=true);
}

module keyboard_cover_front() {
  cube([kb_length, kb_height, 11], center=true);
}

module keyboard_cover_side(height) {
    cube([kb_height - 1, kb_width, height], center=true);
}
