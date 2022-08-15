# Easy Remote with LED Display

![Picture of LED display](docs/remote_display.jpg)

## The Need
As my mom gets older, she is having trouble working the remote for her Roku devices. 

I searched for a senior-friendly remote that worked with Roku but was unable to find one that didn't have way too many tiny buttons on it.

## The Solution
Build a 4-button remote with a large display.

Color code the buttons, LED lights on the keyboard, and text on the display.

This project is tailored to her watching habits, however, it can be easily modified.

In addition to the keypad this implementation will:
- Interact with the TV streaming Netflix every hour to avoid the "Are you still watching message"
- Turn on the bedroom TV automatically
- Turn both televisions off automatically

## The hardware
All the hardware is from [Adafruit](https://www.adafruit.com).

- [Adafruit Matrix Portal Starter Kit - ADABOX 016 Essentials](https://www.adafruit.com/product/4812)
  - You can also get all the parts separately:
    - [Adafruit Matrix Portal](https://www.adafruit.com/product/4745)
	 - [64 x 32 RGB Matrix](https://www.adafruit.com/product/2278)
	 - [LED Diffusion Acrylic](https://www.adafruit.com/product/4749)
	 - [Adhesive Squares](https://www.adafruit.com/product/4813)
	 - [5V 2.4A Power Supply](https://www.adafruit.com/product/1995) + [USB C adapter](https://www.adafruit.com/product/4299)
- [NeoKey 1x4 QT I2C - Four Mechanical Key Switches with NeoPixels - STEMMA QT / Qwiic](https://www.adafruit.com/product/4980)
- [Kailh Mechanical Key Switches - Clicky White - 10 pack - Cherry MX White Compatible](https://www.adafruit.com/product/4955)

The keycap STL file can be found on [Adafruit](https://learn.adafruit.com)
  - [Custom Bluetooth Cherry MX Gamepad](https://learn.adafruit.com/custom-wireless-bluetooth-cherry-mx-gamepad/3d-printing)
  - STL and Fusion 360 source files

The stand is designed in OpenSCAD and the source and STL files are included in the project. For my printer I had to break the stand into two halves. In order to do this there is a mortise/tenon joint to join the halves. If you're printer is big enough you can print the whole unit at once. STL files are provided for each half, the entire stand, and the keyboard cover. No matter how you print it you will need to print the keyboard cover separately.

- Mortise/Tenon Joint library provided by HopefulLlama
  - [Github project](https://github.com/HopefulLlama/JointSCAD)
  - [Thingiverse](https://www.thingiverse.com/groups/openscad/forums/general/topic:14842)
- Threads library provided by rcoyler
  - [Github project](https://github.com/rcolyer/threads-scad)
