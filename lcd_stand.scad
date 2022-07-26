use </home/ntynen/development/openscad_files/remote_parts.scad>
use <openSCAD_lib/threads-scad-master/threads.scad>
$fa = 1;
$fs = 0.4;

// base
l_length = 128;
l_width = 256;
l_height = 5;

// sides
s_length = l_length;
s_width = 5;
s_height = 30;

// top and bottom
tb_length = 266;
tb_width = 5;
tb_height = 30;

// board slot
b_length = 45;
b_width = 6;
b_height = 10;



module back() {
   rotate([0,90,90])
      cube([l_length, l_width / 2, l_height], center=true);
	// Stand
	translate([l_height / 2 - 25,-(l_length / 2) / 2 + s_width / 2 + 5 - 0.001,-l_width / 2 + l_length / 2])
		prism(50, 25, 15);
}

module sides() {
	rotate([0,90,90])
		cube([s_length, s_width, s_height], center=true);
}

module top_bottom() {
	rotate([270,0,0])
		cube([tb_length / 2, tb_width, tb_height]);
}

module dowl() {
	rotate([90,0,90])
		cylinder(r=2, h=4);
}

module dowl_hole() {
	rotate([90,0,90])
		cylinder(r=2.25, h=4);
}

module screw_head() {
    ScrewThread(outer_diam=3, height=3);
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

module left_back_side(){
// Back of case, left side
	difference() {
		back();
		rotate([0,90,90])
		translate([-(l_length / 2 - 8), -(l_width / 4 - 10), 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([(l_length / 2 - 8), -(l_width / 4 - 10), 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([-(l_length /2 - 8), l_width / 4 - 1, 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		rotate([0,90,90])
		translate([(l_length /2 - 8), (l_width / 4 - 1), 0])
			cylinder(r=2.5, h=s_width + 1, center=true);
		translate([(-l_width / 2) + 63, 0, (l_length / 2) - 16])
			dowl_hole();
		translate([(-l_width / 2) + 63 , 0, (-l_length / 2) + 16])
			dowl_hole();
	}

// left side
	translate([(l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 5, 0])
		sides();

// top and bottom
	translate([-l_width / 2 / 2 + s_width / 2 - tb_width, l_height / 2 - 5 ,l_length / 2 + 5 - 0.001])
		top_bottom();
	translate([-l_width / 2 / 2 + s_width / 2 - tb_width, l_height / 2 - 5 ,-l_length / 2  - 0.001])
		top_bottom();
}

module right_back_side() {
//	Back of case, right back plate
//	With dowls 
	difference() {
	back();
	rotate([0,90,90])
		translate([l_length / 2 - 8, l_width / 4 - 10, 0])
		 cylinder(r=2.5, h=s_height, center=true);
	rotate([0,90,90])
		translate([-(l_length / 2 - 8), l_width / 4 - 10, 0])
		 cylinder(r=2.5, h=s_height, center=true);
	rotate([0,90,90])
		translate([l_length /2 - 8, -(l_width / 4 - 1), 0])
		 cylinder(r=2.5, h=s_height, center=true);
	rotate([0,90,90])
		translate([-(l_length /2 - 8), -(l_width / 4 - 1), 0])
		 cylinder(r=2.5, h=s_height, center=true);
	}
	translate([(l_width / 2) / 2 - 0.001, l_length /2 - 64 - 0.001, 46])
		dowl();
	translate([(l_width / 2) / 2 - 0.001, -l_length / 2 + 64, -46])
		dowl();

//	right side
	difference() {
		translate([(-l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 5, 0])
			sides();
		rotate([0,90,0])
		translate([0, l_height / 2 + s_height / 2 + 8, -(l_width / 2) / 2])
			cube([b_length + 5, b_width, b_height], center=true);
	}

// top and bottom
	translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 5 ,l_length / 2 + 5 - 0.001])
		top_bottom();
	translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 5 ,-l_length / 2  - 0.001])
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
left_back_side();
translate([-l_width / 2 - 0.001, 0, 0])
	right_back_side();

//
// Individual pieces of the stand
// For those who's printers can't print
// the entire piece
//

//
// Back of case, right back plate
// With dowls, side, top and bottom
// Keyboard tray attached to side
//

// difference() {
// back();
// rotate([0,90,90])
// 	translate([l_length / 2 - 8, l_width / 4 - 10, 0])
//   	 cylinder(r=2.5, h=s_height, center=true);
// rotate([0,90,90])
// 	translate([-(l_length / 2 - 8), l_width / 4 - 10, 0])
//   	 cylinder(r=2.5, h=s_height, center=true);
// rotate([0,90,90])
// 	translate([l_length /2 - 8, -(l_width / 4 - 1), 0])
//   	 cylinder(r=2.5, h=s_height, center=true);
// rotate([0,90,90])
// 	translate([-(l_length /2 - 8), -(l_width / 4 - 1), 0])
//   	 cylinder(r=2.5, h=s_height, center=true);
// }
// translate([(l_width / 2) / 2 - 0.001, l_length /2 - 64 - 0.001, 46])
// 	dowl();
// translate([(l_width / 2) / 2 - 0.001, -l_length / 2 + 64, -46])
// 	dowl();

// difference() {
// 	translate([(-l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 5, 0])
// 		sides();
// 	rotate([0,90,0])
// 	translate([0, l_height / 2 + s_height / 2 + 8, -(l_width / 2) / 2])
// 		cube([b_length + 5, b_width, b_height], center=true);
// }

// translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 5 ,l_length / 2 + 5 - 0.001])
// 	top_bottom();
// translate([-l_width / 2 / 2 - s_width / 2, l_height / 2 - 5 ,-l_length / 2 + 5 - 0.001])
// 	top_bottom();

//
// Back of case, right back plate
// With dowl holes, side, top and bottom
//

// difference() {
//  	back();
//  	rotate([0,90,90])
//  	translate([-(l_length / 2 - 8), -(l_width / 4 - 10), 0])
// 		cylinder(r=2.5, h=s_width + 1, center=true);
// 	rotate([0,90,90])
// 	translate([(l_length / 2 - 8), -(l_width / 4 - 10), 0])
// 		cylinder(r=2.5, h=s_width + 1, center=true);
// 	rotate([0,90,90])
// 	translate([-(l_length /2 - 8), l_width / 4 - 1, 0])
// 		cylinder(r=2.5, h=s_width + 1, center=true);
// 	rotate([0,90,90])
// 	translate([(l_length /2 - 8), (l_width / 4 - 1), 0])
// 		cylinder(r=2.5, h=s_width + 1, center=true);
// 	translate([(-l_width / 2) + 63, 0, (l_length / 2) - 16])
// 		dowl_hole();
//   	translate([(-l_width / 2) + 63 , 0, (-l_length / 2) + 16])
//   		dowl_hole();
// }

// translate([-(l_width / 2) / 2 - 0.001, l_height / 2 + s_height / 2 - 5, 0])
//    sides();

// 	translate([-l_width / 2 / 2 + s_width / 2 - tb_width, l_height / 2 - 5 ,l_length / 2 + 5 - 0.001])
// 		top_bottom();
// 	translate([-l_width / 2 / 2 + s_width / 2 - tb_width, l_height / 2 - 5 ,-l_length / 2  - 0.001])
// 		top_bottom();
