// SPDX-License-Identifier: MIT

use <lib/threads.scad>
use <lib/JointSCAD.scad>
use <lib/MortiseAndTenonJoint.scad>
$fa = 1;
$fs = 0.4;

// base
l_length = 256;
l_width = 6;
l_height = 128;

// sides
s_length = l_height + 9;
s_width = 5;
s_height = 30;

// top and bottom 
tb_length = 256;
tb_width = 5;
tb_height = 30;

// bottom
b_length = 265 - 10;
b_width = 5;
b_height = 30;

// board slot
c_length = 45;
c_width = 5;
c_height = 6;

// keyboard
k_length = 96;
k_width = 23;
k_height = 5;

// Mortise Joint, base
m_dimensions = [20, 6, l_height / 2];
m_proportions = [0.8, 0.2, 0.8];

// Tenon Joint, base
t_dimensions = [20, 6, l_height / 2 - 5];
t_proportions = [0.8, 0.2, 0.8];

// Bolts & Clearance Holes
bolt_size = 4;

led_bolt = 3;
led_height = 4;

base_screwHole_height = 5;
base_bolt_height = 9;

keyboard_screwHole_height = 5;
keyboard_bolt_height = 6;

//
//  Stand and accessories for 3D Printing
//

// Offsets for LED / back of stand
// difference(){
//  offset_post_with_bolt();
//  rotate([0,180,0])
//  	ScrewHole(outer_diam=bolt_size, height=base_screwHole_height);
// }

// Bolt for securing LED to back of stand
// MetricBolt(bolt_size, base_bolt_height);

// Bolt for securing keyboard to tray
// MetricBolt(bolt_size, keyboard_bolt_height);

// Keyboard Tray Cover
// keyboard_cover(4, 19) key_holes();

//
// The entire stand
// For larger 3D printers
// You will need to print the keyboard cover separately
//

base_left_side();
translate([-l_length / 2 - 0.001, 0, 0])
	base_right_side();

//
// Individual pieces of the stand
// For smaller 3D printers
//

// Base of case, left back plate
// back, side, top, bottom, tenon joint
// base_left_side();

// Back of case, right back plate
// back, side, top, bottom, keyboard tray, mortise joint
// base_right_side();

//
// Modules
//

module base() {
   cube([l_length / 2, l_width,  l_height], center=true);
	// Stand
 	translate([-l_length / 2 + l_height - 20  ,-(l_height / 2) / 2 + s_width / 2 + 2 - 0.001, -l_height / 2 - 4.5 ])
 		stand(50, 25, 15);
}

// Thank you Adafruit for the hardware, the support, and the community!
module base_design() {
	scale([.15,.15,3])
		surface(file = "images/adafruit_logo_transparent_small.png", center = true, invert=false);
}

module sides() {
	rotate([0,90,90])
		cube([s_length, s_width, s_height], center=true);
}

module top() {
	rotate([270,0,0])
		cube([tb_length / 2, tb_width, tb_height], center=true);
}

module right_bottom() {
	rotate([270,0,0])
	cube([tb_length / 2, tb_width, tb_height + 20], center=true);

	translate([-tb_length / 2 / 2 + 48.25, tb_height + 6.46 -  0.001, -b_height / 2 + 15])
		keyboard_tray();
}

module left_bottom() {
	rotate([270,0,0])
	cube([tb_length / 2, tb_width, tb_height + 20], center=true);

	translate([tb_length / 2 / 2 + 2.3 - 0.001, tb_height - 15 - 0.001, -b_height / 2 + 18.5])
		cube([5,20,12], center=true);
}

module offset_post() {
  cylinder(r=3, h=12, center=true);
}

module offset_base() {
    cube([8,8,10], center=true);
}

module offset_post_with_bolt() {
  translate([0, 0, 17 - 0.001])
    ScrewThread(outer_diam=led_bolt, height=led_height);
  translate([0, 0, 11 - 0.001])
    offset_post();
  translate([0,0,0 - 0.001])
    offset_base();
}

module stand(l, w, h){
   rotate([0,0,0])
   polyhedron(
      points=[[0,0,0], [l,0,0], [l,w,0], [0,w,0], [0,w,h], [l,w,h]],
      faces=[[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
   );
}

module mounting_holes() {
	cylinder(r=2.5, h=s_width + 1, center=true);
}

module circuit_board() {
	cube([c_length + 10, b_width + 10, b_height], center=true);
}

module kb_right_side() {
	cube([5.1, k_width + 23 , c_height + 6], center=true);
}

module kb_left_side() {
	cube([3, k_width + 3 , c_height + 6], center=true);
}

module kb_front() {
	cube([k_length , 3, c_height + 6], center=true);
}

module keyboard_tray(){
	cube([k_length, k_width, k_height], center=true);

	translate([k_length / 2 - 6, -1, k_height - 0.001])
	difference() {
		cylinder(r=3.5, h=keyboard_screwHole_height + 1, center=true);
			ScrewHole(outer_diam=bolt_size, height=keyboard_screwHole_height);
	}

	translate([-(k_length / 2 - 5), -1, k_height - 0.001])
	difference() {
		cylinder(r=3.5, h=keyboard_screwHole_height + 1, center=true);
			ScrewHole(outer_diam=bolt_size, height=keyboard_screwHole_height);
	}

	translate([-k_length / 5  , -k_width / 2 + 4, k_height - 0.001])
		cylinder(r=2, h=k_height, center=true);
	translate([-k_length / 5, k_width / 2 - 4, k_height - 0.001])
		cylinder(r=2, h=k_height, center=true);

	translate([k_length / 4 - 4, -k_width / 2 + 4, k_height - 0.001])
		cylinder(r=2, h=k_height, center=true);
	translate([k_length / 4 - 4, k_width / 2 - 4, k_height - 0.001])
		cylinder(r=2, h=k_height, center=true);

	translate([-k_length / 2 - 2.5 - 0.001, -k_width / 2 + 3 - 0.001, k_height - 1.5])
		kb_right_side();
	translate([k_length / 2 + 1.5 - 0.001, -k_width / 2 + 13 - 0.001, k_height - 1.5])
		kb_left_side();

	translate([0, k_width / 2 + 1.5 - 0.001 , k_height - 1.5])
		kb_front();
}

module key_holes(){
	cube([15, 16, 5], center=true);
}

module keyboard_cover(num, space) {
	difference() {
		cube([k_length - 1, k_width - 1 , 2], center=true);
		for (i = [0 : num - 1]) 
			translate([-k_length / 2 / 2  - 5 + space*i, 0, 0])
				children(0);
		translate([-k_length / 2 + 5.5, -1, 0])
			cylinder(r=3, h=3, center=true);
		translate([k_length / 2 - 5, -1, 0])
			cylinder(r=3, h=3, center=true);
	}
}

module base_left_side(){
	difference() {
 		base();
		rotate([90,90,0])
			base_design();
		rotate([0,90,90])
		translate([-(l_height / 2 - 8), -(l_length / 4 - 8), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([(l_height / 2 - 8), -(l_length / 4 - 8), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([-(l_height / 2 - 8), (l_length / 4), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([(l_height / 2 - 8), (l_length / 4), 0])
			mounting_holes();
	}
 	translate([-l_length / 2 / 2 - 20, -3, -l_height / 2 / 2])
		tenon(t_dimensions, t_proportions);

	translate([l_length / 2 - l_height / 2 + 2.3 - 0.001, s_height / 2 - l_width / 2, 0])
		sides();

	translate([-l_length / 2  / 2 + l_height / 2 + s_width / 2 / 2 - 1.25,  l_width / 2 + s_width / 2 + 6.5 - 0.001 ,l_height / 2 + 2 - 0.001])
		top();
	translate([0, b_height / 2 + 7, -l_height / 2 - 2 - 0.001])
		left_bottom();
}

module base_right_side() {
	difference() {
		base();
		rotate([90,90,0])
			base_design();
		rotate([0,90,90])
		translate([-(l_height / 2 - 8), (l_length / 4 - 8), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([(l_height / 2 - 8), (l_length / 4 - 8), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([-(l_height / 2 - 8), -(l_length / 4), 0])
			mounting_holes();
		rotate([0,90,90])
		translate([(l_height / 2 - 8), -(l_length / 4), 0])
			mounting_holes();
 		translate([l_length / 2 / 2 - 20, -3, -l_height / 2 / 2])
			cube([20,6,l_height / 2]); // This holds the mortise joint
	}
 	translate([l_length / 2 / 2 - 20, -3, -l_height / 2 / 2])
		mortise(m_dimensions, m_proportions);

 	difference() {
		translate([-(l_length / 2 - l_height / 2 + 2.3) - 0.001, s_height / 2 - l_width / 2, 0])
			sides();
		rotate([0,90,0])
		translate([0, -s_width / 2 + 24 , -l_length / 2 / 2 - 2])
			circuit_board();
 	}

	translate([-l_length / 2  / 2 + l_height / 2 + s_width / 2 / 2 - 1.25,  l_width / 2 + s_width / 2 + 6.5 - 0.001 ,l_height / 2 + 2 - 0.001])
		top();
	translate([0, b_height / 2 + 7, -l_height / 2 - 2 - 0.001])
		right_bottom();
}

