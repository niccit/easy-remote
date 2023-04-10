// SPDX-License-Identifier: MIT
$fa = 1;
$fs = 0.4;

// keyboard tray
kb_length = 76.2;
kb_width = 21.59;
kb_height = 4;

front_length = kb_length;
front_width = 17;
front_height = 0.75;

mounting_hole_diam = 2.45;
mounting_hole_height = 4;
mounting_hole_distance = 2.51;

// ### Begin Modules ###

module base_cube() {
    difference() {
        cube([kb_length + 10, kb_width + 10, kb_height], center=true);
        translate([0, 0, kb_height])
            cube([kb_length + 8, kb_width + 8, kb_height + 1]);
    }
}

// For fitting top and bottom together
module base_hollow_outline() {
    difference() {
        cube([kb_length + 7, kb_width + 7, kb_height], center=true);
        cube([kb_length + 5, kb_width + 5, kb_height + 1], center=true);
    }
}

module base_with_snapfit() {
    difference() {
        base_cube();
        translate([0, 0, kb_height - 1.5])
            base_hollow_outline();
    }
}

module complete_base() {
    difference() {
        base_with_snapfit();
        translate([-kb_length/2 + 19.05, kb_width/2 - mounting_hole_distance, 0])
            cylinder(d=mounting_hole_diam, h=mounting_hole_height, center=true);
        translate([kb_length/2 - 19.05, kb_width/2 - mounting_hole_distance, 0])
            cylinder(d=mounting_hole_diam, h=mounting_hole_height, center=true);
        translate([-kb_length/2 + 19.05, -kb_width/2 + mounting_hole_distance, 0])
            cylinder(d=mounting_hole_diam, h=mounting_hole_height, center=true);
        translate([kb_length/2 - 19.05, -kb_width/2 + mounting_hole_distance, 0])
            cylinder(d=mounting_hole_diam, h=mounting_hole_height, center=true);
    }
}

module keyboard_cover(num, space) {
  difference() {
    cube([kb_length + 6.25, kb_width + 6, kb_height - 1], center=true);
		for (i = [0 : num - 1])
            if (num == 4) {
                translate([-kb_length / 2 + 9.6 + space*i, 0, 0])
                    children(0);
            }
            else {
                translate([-kb_length / 2 + 29 + space*i, 0, 0])
                    children(0);
            }
	}
    // front
    rotate([90,0,0])
    translate([0, -front_width / 2 + 1.5, kb_width / 2 + 3 - 0.001])
        cube([front_length + 6.25, front_width, front_height], center = true);
    // back
    rotate([90,0,0])
    translate([0, -front_width / 2 + 1.5, -kb_width / 2 - 3 - 0.001])
        cube([front_length + 6.25, front_width, front_height], center = true);
    // left side
    rotate([90, 0, 90])
    if (num == 4) {
        translate([0, -front_width / 2 + 5.25, kb_length / 2 + 3 - 0.001])
        cube([kb_width + 6.75, front_width - 7.5, front_height], center = true);
    }
    else {
        translate([0, -front_width / 2 + 1.5, kb_length / 2 + 3 - 0.001])
        cube([kb_width + 6.75, front_width, front_height], center = true);
    }
    // right side
   rotate([90, 0, 90])
   translate([0, -front_width / 2 + 5.25, -kb_length / 2 - 3 - 0.001])
        cube([kb_width + 6.75, front_width - 7.5, front_height], center = true);
}


module key_holes(){
  cube([16, 16, kb_height], center=true);
}

// ### End Modules ###

// Construction of the parts

show_base = 0;
show_top = 0;
show_all = 1;
do_rotate = 0;
keys = 4;


if (show_base == 1) {
    if (do_rotate == 1) {
        rotate([180, 0, 0])
            complete_base();
    }
    else {
        complete_base();
    }
}

if (show_top == 1) {
    if (do_rotate == 1) {
        rotate([180, 0, 0])
            keyboard_cover(keys, 19) key_holes();
    }
    else {
        keyboard_cover(keys, 19) key_holes();
    }
}

if (show_all == 1) {
    complete_base();
    rotate([180, 0, 0])
    translate([kb_length + 20, 0, 0])
        keyboard_cover(4, 19) key_holes();
}


