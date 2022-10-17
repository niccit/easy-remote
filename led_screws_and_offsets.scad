// SPDX-License-Identifier: MIT
//
// Offsets for mounting display to stand and
// screws for securing display to offsets and keyboard cover
//

use <lib/threads.scad>

$fa = 1;
$fs = 0.4;

// Bolts & Clearance Holes
bolt_size = 4;
offset_bolt = 3;
offset_bolt_height = 6;
kb_bolt_height = 6;
base_bolt_height = 12;
base_screwHole_height = 9;

// Offsets for LED / back of stand
//
offset_with_bolt();

// Bolt for securing LED to back of stand
//
translate([0, 15, -10])
	MetricBolt(bolt_size, base_bolt_height);

// Bolt for securing keyboard cover
//
translate([0, 30, -10])
	MetricBolt(bolt_size, kb_bolt_height);





module offset_base() {
	difference() {
    cylinder(r=4, h=15, center=true);
			ScrewHole(outer_diam=bolt_size, height=base_screwHole_height);
	}
}

module offset_with_bolt() {
	translate([0, 0, 5 - 0.001])
	 ScrewThread(outer_diam=offset_bolt, height=offset_bolt_height);
	rotate([0,180,0])
	translate([0,0,2 - 0.001])
	 offset_base();
}
