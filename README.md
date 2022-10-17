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
- Turn on the primary and secondary TVs automatically

## How it works
The project is coded in <a href="https://circuitpython.org/" target="_blank">CircuitPython</a>

You will need to create your own secrets file based on the example file included in the project. Documentation for building a secrets file can be found <a href="https://learn.adafruit.com/electronic-history-of-the-day-with-pyportal/code-walkthrough-secrets-py" target="_blank">here.</a>

To better understand how to interact with the Roku devices, please visit the <a href="https://developer.roku.com/en-ca/docs/developer-program/debugging/external-control-api.md" target="_blank">Roku Developers : External Control Protocol (ECP) documentation.</a>

All configurable data is stored in the data file:
- device_urls : One or more Roku devices available on the network
- shows : The shows/channels the person using this remote likes to watch
- channels :  The Roku channel names
- channel_numbers : The corresponding Roku channel IDs - see the ECP for how to get a channel ID
- frndly_guide_position : Unfortunately, Frndly TV app currently doesn't support the Roku search controls. For now you have to find your channel in the guide and count how many down from the top it is and us it for this value.
- netflix_search_int : Netflix doesn't put you back to the starting position on the search grid, so you have to note how many moves right it is from the last letter in your search to the program you want to select.
- primary_tv_start_time : The time, stored in an array [hh, mm], you want the primary television to turn on each day
- secondary_tv_start_time: The time, stored in an array [hh, mm], you want the secondary television to turn on each day

### Why I chose to use a data file?
I wanted the code to be flexible with as little hard coding as possible. It's much easier to edit the data file then to make changes directly in the code.

## The hardware
All the hardware is from <a href="https://www.adafruit.com" target="_blank">Adafruit.</a>

- <a href="https://www.adafruit.com/product/4812" target="_blank">Adafruit Matrix Portal Starter Kit - ADABOX 016 Essentials</a>
  - You can also get all the parts separately:
    - <a href="https://www.adafruit.com/product/4745" target="_blank">Adafruit Matrix Portal</a>
    - <a href="https://www.adafruit.com/product/2278" target="_blank">64 x 32 RGB Matrix</a>
    - <a href="https://www.adafruit.com/product/4749" target="_blank">LED Diffusion Acrylic</a>
    - <a href="https://www.adafruit.com/product/4813" target="_blank">Adhesive Squares</a>
    - <a href="https://www.adafruit.com/product/1995" target="_blank">5V 2.4A Power Supply</a> + <a href="https://www.adafruit.com/product/4299" target="_blank">USB C adapter</a>
- <a href="https://www.adafruit.com/product/4980" target="_blank">NeoKey 1x4 QT I2C - Four Mechanical Key Switches with NeoPixels - STEMMA QT / Qwiic</a>
- <a href="https://www.adafruit.com/product/4955" target="_blank">Kailh Mechanical Key Switches - Clicky White - 10 pack - Cherry MX White Compatible</a>


## 3D printing
The stand is designed in OpenSCAD and the source and STL files are included in the project. For my printer I had to break the stand into two halves. In order to do this there is a mortise/tenon joint to join the halves. If your printer is big enough you can print the whole unit at once. STL files are provided for each half, the entire stand, and the keyboard cover.

No matter how you print it you will need to print the offsets, screws, and keyboard cover separately.
- If you have M3 screws and offsets you can forego printing those
- if you have M4 screws you can forego printing the screws
- The LED display has M3 threaded holes
- The offsets and keyboard tray use M4 threaded holes
  - I went up to M4 because I found that size printed more reliably

I have not included supports in the STL files. You will need to add supports into your slicer or the print will not come out as intended.

- Filament and Slicing:
   - PLA for the stand
      - Color: Color change purple to blue
      - Extruder: .4/240c
      - Extruder Temp: 210c
      - Platform Temp: 45c
      - Supports:
         - Yes for main case
            - Tree-like
            - Auto generated
         - No for keyboard cover
      - Brim: Yes, no brim generated in holes
   - PETG for the keyboard cover
      - Color: Transparent
      - Extruder: .4/265c
      - Extruder Temp: 240c
      - Platform Temp: 80c
      - Supports: Yes
         - Linear
         - Manually generated
      - Raft: Yes

- Joint library provided by HopefulLlama
  - <a href="https://github.com/HopefulLlama/JointSCAD" target="_blank">Github project</a>
  - <a href="https://www.thingiverse.com/groups/openscad/forums/general/topic:14842" target="_blank">Thingiverse</a>
- Threads library provided by rcoyler
  - <a href="https://github.com/rcolyer/threads-scad" target="_blank">Github project</a>
