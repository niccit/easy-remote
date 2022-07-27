use <lib/threads.scad>
use <lib/JointSCAD.scad>
use <lib/MortiseAndTenonJoint.scad>
$fa = 1;
$fs = 0.4;

// base
l_length = 128;
l_width = 256;
l_height = 6;

// sides
s_length = l_length;
s_width = 5;
s_height = 30;

// top and bottom
tb_length = 261;
tb_width = 5;
tb_height = 30;

// board slot
b_length = 45;
b_width = 6;
b_height = 10;

// Joint 
j_dimensions = [10, 4, 10];
j_proportions = [0.8, 0.2, 0.8];

module base() {
   rotate([0,90,90])
      cube([l_length, l_width / 2, l_height], center=true);
	// Stand
 	translate([l_height / 2 - 25,-(l_length / 2) / 2 + s_width / 2 + 5 - 0.001, -l_width / 2 + l_length / 2 - 5])
 		prism(50, 25, 15);
}

// Thank you Adafruit for the hardware, the support, and the community!
module base_design() {
	scale([.5, .5, 3])
		surface(file = "images/adafruit_logo_transparent_small.png", center = true);
}

module sides() {
	rotate([0,90,90])
		cube([s_length, s_width, s_height], center=true);
}

module top_bottom() {
	rotate([270,0,0])
		cube([tb_length / 2, tb_width, tb_height]);
}

module screw_head() {
    ScrewThread(outer_diam=3, height=3);
}

module cable_outlet() {
	rotate([90,0,0])
		cube([8, b_width, 8], center=true);
}

module offset_post() {
  cylinder(r=1.5, h=20);
}

module offset_base() {
    cube([5,5,10], center=true);
}

module offset_post_with_screw() {
  translate([0, 0, 20 - 0.001])
    screw_head();
  translate([0, 0, 0 - 0.001])
    offset_post();
  translate([0,0,0 - 0.001])
    offset_base();
}

module prism(l, w, h){
   rotate([0,0,0])
   polyhedron(
      points=[[0,0,0], [l,0,0], [l,w,0], [0,w,0], [0,w,h], [l,w,h]],
      faces=[[0,1,2,3],[5,4,3,2],[0,4,5,1],[0,3,4],[5,2,1]]
   );
}

module keyboard_tray(){

}

module base_left_side(){
	difference() {
		base();
		rotate([90,90,0])
			base_design();
		rotate([0,90,90])
		translate([-(l_length / 2 - 8), -(l_width / 4 - 10), 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([(l_length / 2 - 8), -(l_width / 4 - 10), 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([-(l_length /2 - 8), l_width / 4 , 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([(l_length /2 - 8), l_width / 4, 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
	}
	translate([-l_width / 2 + 55 - 0.001, -l_height / 2 + 1, s_height / 2 - 20])
		tenon(j_dimensions, j_proportions);

	translate([(l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 6, 0])
		sides();

	translate([-l_width / 2 / 2 + s_width / 2 - 2.5,  l_height / 2 - 6 - 0.001 ,l_length / 2 + 5 - 0.001])
		top_bottom();
	translate([-l_width / 2 / 2 + s_width / 2 - 2.5, l_height / 2 - 6 - 0.001 ,-l_length / 2  - 0.001])
		top_bottom();
}

module base_right_side() {
	difference() {
		base();
		rotate([90,90,0])
			base_design();
		rotate([0,90,90])
			translate([l_length / 2 - 8, l_width / 4 - 10, 0])
			 cylinder(r=2.5, h=s_height, center=true);
		rotate([0,90,90])
			translate([-(l_length / 2 - 8), l_width / 4 - 10, 0])
			 cylinder(r=2.5, h=s_height, center=true);
		rotate([0,90,90])
			translate([l_length /2 - 8, -(l_width / 4), 0])
			 cylinder(r=2.5, h=s_height, center=true);
		rotate([0,90,90])
			translate([-(l_length /2 - 8), -(l_width / 4), 0])
			 cylinder(r=2.5, h=s_height, center=true);
		translate([l_length / 2 - 4, -l_height / 2 + 1, s_height / 2 - 20])
			cube([10,4,10]);
	}
	translate([l_length / 2 - 10, -l_height / 2 + 1, s_height / 2 - 20])
		mortise(j_dimensions, j_proportions);

	difference() {
		translate([(-l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 6, 0])
			sides();
		rotate([0,90,0])
		translate([0, l_height / 2 + s_height / 2 + 8, -(l_width / 2) / 2])
			cube([b_length + 5, b_width + 5, b_height], center=true);
		translate([(-l_width / 2) / 2 ,s_height / 2,-s_length / 2 + 20])
			cable_outlet();
	}

	translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 6 - 0.001 ,l_length / 2 + 5 - 0.001])
		top_bottom();
	translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 6 - 0.001 ,-l_length / 2  - 0.001])
		top_bottom();
}

//
// Offsets and bolts for securing display to stand
// 

// Offsets
// difference(){
//  offset_post_with_screw();
//  rotate([0,180,0])
//  translate([0,.25,0])
//    ScrewHole(outer_diam=3.4, height=5);
// }

// Bolt
// MetricBolt(3, 9);

// The entire unit, if your printer is big enough
// base_left_side();
// translate([-l_width / 2 - 0.001, 0, 0])
// 	base_right_side();

//
// Individual pieces of the stand
// For those who's printers can't print
// the entire stand
//

//
// Base of case, left back plate
// back, side, top, bottom, tenon joint

// base_left_side();

// Back of case, right back plate
// back, side, top, bottom, keyboard tray, mortise joint
 
// base_right_side();
