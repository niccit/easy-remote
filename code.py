# SPDX-License-Identifier: MIT
import random
# This is a very simple remote, designed for individuals with difficulty navigating
# all the different streaming applications
# It was designed to help a senior have less frustration while trying to watch television

import time
import board
import busio
import digitalio
import re
import displayio
import adafruit_requests as requests
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_neokey.neokey1x4 import NeoKey1x4
from adafruit_display_text.label import Label
from adafruit_matrixportal.network import Network

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
DISPLAY_BITPLANES = 6
FONT = bitmap_font.load_font("/fonts/RobotoMono-Regular-8.pcf")

# Get Wifi information from secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there")
    raise

# Get data needed to launch shows and interact with devices
try:
    from data import data
except ImportError:
    print("Cannot import data file")
    raise

# --- Setup  ---

# Network
esp32_cs = digitalio.DigitalInOut(board.ESP_CS)
esp32_ready = digitalio.DigitalInOut(board.ESP_BUSY)
esp32_reset = digitalio.DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
network = Network(status_neopixel=board.NEOPIXEL, esp=esp, debug=False)
requests.set_socket(socket, esp)

# Get what we need from the data file
hosts = data["device_hosts"]
port = data["service_port"]
current_shows = data["shows"]
current_channels = data["channels"]
channel_ids = data["channel_numbers"]
guide_position = data["frndly_guide_position"]
netflix_search_int = data["netflix_search_int"]
paramount_search_int = data["paramount_search_int"]
primary_tv_start_time = data["primary_tv_start_time"]
primary_tv_end_time = data["primary_tv_end_time"]
secondary_tv_start_time = data["secondary_tv_start_time"]
secondary_tv_end_time = data["secondary_tv_end_time"]
update_delay = data["update_delay"]
interact_delay = data["interact_delay"]
# For testing onlyu!
test_mode = data["test_mode"]
test_delay = data["test_delay"]

# Setting necessary defaults
second_tv = False
default_display = False
busy = False
cur_time = []
last_check = None
interact_check = None
display_array = []
primary_device_state = None
secondary_device_state = None
primary_active_app = None
secondary_active_app = None
netflix_channel_id = int(channel_ids[0])
# For testing only!
last_test_check = None

# URLs
url_1 = ("http://" + hosts[0] + ":" + port + "/")
url_2 = ("http://" + hosts[1] + ":" + port + "/")

# Host IPs, for ping check
host_1_ip = hosts[0]
host_2_ip = hosts[1]

# Shows for each streaming service
show_1 = current_shows[0]
show_2 = current_shows[1]
show_3 = current_shows[2]

# Streaming channels
channel_1 = current_channels[0]
channel_2 = current_channels[1]
channel_3 = current_channels[2]

# Streaming channel IDs
channel_id_1 = channel_ids[0]
channel_id_2 = channel_ids[1]
channel_id_3 = channel_ids[2]


# --- Roku API Calls ---
# Home
home = "keypress/home"
#  Right
right = "keypress/right"
#  Left
left = "keypress/left"
# Up
up = "keypress/up"
#  Down
down = "keypress/down"
# Back
back = "keypress/back"
#  select
select = "keypress/select"
#  volume up
vol_up = "keypress/volumeup"
#  volume down
vol_down = "keypress/volumedown"
#  power on
pwr_on = "keypress/poweron"
#  power off
pwr_off = "keypress/poweroff"
# Launch a channel
launch = "launch/"
# Query Active Application
active_app = "query/active-app"
# Query Device State
query_media = "query/media-player"
# Test Call for socket availability
dev_check = "query/chanperf"

# --- Display ---
matrix = Matrix()
display = matrix.display

group = displayio.Group()
bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_BITPLANES)
color = displayio.Palette(6)
color[0] = 0x000000  # black background
color[1] = 0XFF0000  # red = Netflix
color[2] = 0x00FFFF  # blue = Paramount+
color[3] = 0x008000  # green = Frndly
color[4] = 0xFFFFFF  # white =  default color
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
group.append(tile_grid)
display.show(group)

# --- Set up the keyboard ---
i2c_bus = board.STEMMA_I2C()
neokey = NeoKey1x4(i2c_bus, addr=0x30)

# Set colors for the keyboard
neokey.pixels[0] = color[1]
neokey.pixels[1] = color[2]
neokey.pixels[2] = color[3]
neokey.pixels[3] = color[4]


# --- Helper Methods for the Display ---

# Update the time, synchronize board clock, and return current time
def update_time():
    global cur_time

    while cur_time is None:
        try:
            cur_time = time.localtime()
        except RuntimeError as e:
            print("update_time: An error occurred, retrying ... ", e)
            continue

    tick_tock = 0
    while tick_tock <= 2:
        try:
            network.get_local_time()  # Synchronize Board's clock to internet
            tick_tock = 3
        except RuntimeError as r:
            print("unable to synchronize board clock to internet. Error:", r, "attempt", counter,
                  "of 3, will retry in 2 seconds")
            continue

        tick_tock += 1
        time.sleep(2)

    return cur_time


# Set loading display message
# Used during initial start and each recheck
def set_loading_display_msg():
    global display_array, default_display

    load1 = Label(
        font=FONT,
        color=color[4],
        text="{0}".format("Loading"))
    bbx, bby, bbwidth, bbh = load1.bounding_box
    load1.x = round(display.width / 2 - bbwidth / 2)
    load1.y = 4

    load2 = Label(
        font=FONT,
        color=color[4],
        text="{0}".format("Please Wait"))
    bbx2, bby2, bbwidth2, bbh2 = load2.bounding_box
    load2.x = round(display.width / 2 - bbwidth2 / 2)
    load2.y = 18

    clear_display()
    display_array = ["load1", "load2"]

    group.append(load1)
    group.append(load2)

    default_display = False


# Set the default display when active
# Color coded by show/channel
def set_default_display_msg():
    global display_array, default_display

    if default_display is False:
        hello1 = Label(
            font=FONT,
            color=color[4],
            text="{0}".format("What to Watch"))
        bbx, bby, bbwidth, bbh = hello1.bounding_box
        hello1.x = round(display.width / 2 - bbwidth / 2)
        hello1.y = 4

        hello2 = Label(
            font=FONT,
            color=color[1],
            text="{0}".format(show_1))
        bbx2, bby2, bbwidth2, bbh2 = hello2.bounding_box
        hello2.x = round(display.width / 2 - bbwidth2 / 2)
        hello2.y = 11

        hello3 = Label(
            font=FONT,
            color=color[2],
            text="{0}".format(show_2))
        bbx3, bby3, bbwidth3, bbh3 = hello3.bounding_box
        hello3.x = round(display.width / 2 - bbwidth3 / 2)
        hello3.y = 18

        hello4 = Label(
            font=FONT,
            color=color[3],
            text="{0}".format(show_3))
        bbx4, bby4, bbwidth4, bbh4 = hello4.bounding_box
        hello4.x = round(display.width / 2 - bbwidth4 / 2)
        hello4.y = 25

        clear_display()
        display_array = ["hello1", "hello2", "hello3", "hello4"]

        group.append(hello1)
        group.append(hello2)
        group.append(hello3)
        group.append(hello4)

        default_display = True


# Set the display while launching a show
# The display will read "Now Playing \r <selected show>"
def set_watching_display(channel):
    global display_array, default_display

    # Default show color
    show_color = color[4]
    # Default show text
    show_text = "{0}".format("Default Show Text Here")

    if channel:
        channel = channel

    # Set the second line of the display based on the channel chosen
    if channel is channel_1:
        show_text = "{0}".format(show_1)
        show_color = color[1]
    elif channel is channel_2:
        show_text = "{0}".format(show_2)
        show_color = color[2]
    elif channel is channel_3:
        show_text = "{0}".format(show_3)
        show_color = color[3]

    line1 = Label(
        font=FONT,
        color=color[4],
        text="{0}".format("Now Playing"))
    bbx1, bby1, bbwidth1, bbh1 = line1.bounding_box
    line1.x = round(display.width / 2 - bbwidth1 / 2)
    line1.y = 8

    line2 = Label(
        font=FONT,
        color=show_color,
        text=show_text)
    bbx2, bby2, bbwidth2, bbh2 = line2.bounding_box
    line2.x = round(display.width / 2 - bbwidth2 / 2)
    line2.y = 24

    clear_display()
    display_array = ["line1", "line2"]

    group.append(line1)
    group.append(line2)

    default_display = False


# Clear the display based
def clear_display():
    global display_array

    for i in range(len(display_array)):
        group.pop()


# --- Helper methods for other tasks not related to the Roku or Display ---

# Convert a show name to an array for searching
def get_show_search_array(show):
    if show is None:
        print("get_show_search_array: No show to parse, please specify a show name")

    show_to_split = show.split()
    show_to_split_length = len(show_to_split)
    show_array = []
    counter = 0
    for word in show_to_split:
        counter += 1
        if counter < show_to_split_length:
            show_array += list(word)
            show_array += " "
        else:
            show_array += list(word)
    return show_array


#  --- Helper methods for interacting with Roku ---
# After a while an OutOfRetries
# Have each method call this prior to making the actual call to the device
def retry_socket_connection(url):
    socket_available = False
    retries = 0

    if url:
        device_url = url
    else:
        device_url = url_1

    while socket_available is False:
        print("retry_socket_connection: testing availability of socket")
        try:
            requests.get(device_url + dev_check)
            socket_available = True
        except Exception as e:
            print("Caught generic exception", e, "retrying socket connection in 2 seconds, attempt:", retries)
            retries += 1
            time.sleep(2)
            pass

    return socket_available


# Use in-channel search to locate show to watch
# Using search as a more reliable way to find what to watch
def search_program(url, show, channel):
    global busy

    if not show:
        print("search_program: Please provide a show to use in search")

    if url:
        device_url = url
    else:
        device_url = url_1

    if channel:
        channel = channel

    # If using Netflix, the search will remain on the last letter
    # of the searched show, so the amount we need to navigate to select
    # the show changes.
    # For ease of use I've stored this value in data.py
    if channel is channel_1:
        search_int = netflix_search_int
    elif channel is channel_2:
        search_int = paramount_search_int
    else:
        search_int = 0

    busy = True

    socket_status = retry_socket_connection(device_url)

    if socket_status is True:
        for i in show:
            requests.post(device_url + "keypress/Lit_" + i)
            time.sleep(0.25)

        time.sleep(1)

        for x in range(search_int):
            requests.post(device_url + right)
            time.sleep(0.25)

        requests.post(device_url + select)
        time.sleep(1)

    busy = False


# Launch the Netflix app on target device
# Select the last used profile
# Bring up the left nav menu
# Execute search for chosen show and select
def launch_netflix(url):
    global second_tv, busy

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        app = primary_active_app
        state = primary_device_state
    else:
        app = secondary_active_app
        state = secondary_device_state

    if state is "active":
        busy = True
        # Check and see if Netflix is active, if so exit the app before starting new show
        if app == netflix_channel_id:
            exit_netflix(device_url)

        socket_status = retry_socket_connection(device_url)

        if socket_status is True:
            print("launching", show_1, "on", channel_1, "on device", device_url)

            if second_tv is True:
                second_tv = False
            else:
                set_watching_display(channel_1)

            requests.post(device_url + launch + channel_id_1)  # launch Netflix
            time.sleep(20)
            requests.post(device_url + select)  # select the active profile
            time.sleep(5)
            requests.post(device_url + left)  # open the left nav menu
            time.sleep(1)
            requests.post(device_url + up)  # navigate to search
            time.sleep(1)
            requests.post(device_url + select)  # enter search
            time.sleep(1)
            # Depending on what type of Roku you're using, you might need this extra navigation
            #    requests.post(device_url + left)  # Move from Top Searches to the search box
            #    time.sleep(1)
            search_program(device_url, show_1, channel_1)
            time.sleep(1)
            requests.post(device_url + select)  # Star the selected show

            time.sleep(2)
            set_active_app(device_url)

            time.sleep(2)
            set_default_display_msg()
        busy = False


# Because Netflix never leaves you in a known state
# we need to exit the app every time we turn off the TV or change apps
def exit_netflix(url):
    global busy

    if url:
        device_url = url
    else:
        device_url = url_1

    busy = True
    socket_status = retry_socket_connection(device_url)
    if socket_status is True:
        print("exiting ", channel_1)
        for x in range(4):  # Get back to left nav
            requests.post(device_url + back)
            time.sleep(1)
        requests.post(device_url + down)  # Navigate to home, our start point
        time.sleep(0.25)
        requests.post(device_url + select)  # Select it to save it
        time.sleep(0.5)
        requests.post(device_url + back)  # Return to left nav
        time.sleep(0.25)
        for i in range(3):  # Move up to the profile
            requests.post(device_url + up)
            time.sleep(0.5)
        requests.post(device_url + select)  # Select it to land on profiles page

    busy = False


# Launch Paramount+
# Choose second profile
# Open left nav
# Move to search
# Execute search for show and select
def launch_paramount(url):
    global second_tv, busy

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        state = primary_device_state
        app = primary_active_app
    else:
        state = secondary_device_state
        app = secondary_active_app

    busy = True
    if state is "active":
        if app == netflix_channel_id:
            exit_netflix(url=device_url)

        socket_status = retry_socket_connection(device_url)

        if socket_status is True:
            print("launching ", show_2, "on ", channel_2, " on device ", device_url)

            # Set the display to indicate what we're watching
            if second_tv is True:
                second_tv = False
            else:
                set_watching_display(channel=channel_2)

            requests.post(device_url + launch + channel_id_2)  # launch Paramount+
            time.sleep(10)
            requests.post(device_url + right)  # Navigate to second profile
            time.sleep(1)
            requests.post(device_url + select)  # Select second profile
            time.sleep(5)
            requests.post(device_url + left)  # Access lef nav
            time.sleep(1)
            requests.post(device_url + up)  # Move up to enter Search
            time.sleep(1)
            requests.post(device_url + select)  # Enter Search
            time.sleep(1)
            search_program(url=device_url, show=show_2, channel=channel_2)
            time.sleep(1)
            requests.post(device_url + select)  # Select the searched show
            time.sleep(1)
            requests.post(device_url + select)  # Start playing the show

            time.sleep(2)
            set_active_app(device_url)

            time.sleep(2)
            set_default_display_msg()
    busy = False


# Launch FrndlyTV
# Navigate to the selected channel in the guide
# Select that channel
# Select Watch Live
def launch_frndly(url):
    global second_tv, busy

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        state = primary_device_state
        app = primary_active_app
    else:
        state = secondary_device_state
        app = secondary_active_app

    busy = True

    if state is "active":
        if app == netflix_channel_id:
            exit_netflix(device_url)

        socket_status = retry_socket_connection(device_url)

        if socket_status is True:
            print("launching ", show_3, " on ", channel_3, " on device ", device_url)

            if second_tv is True:
                second_tv = False
            else:
                set_watching_display(channel=channel_3)

            requests.post(device_url + launch + channel_id_3)  # Launch FrndlyTV
            time.sleep(10)
            # Since FrndlyTV search is non-standard, we can't search without it
            # being clunky and downright ugly
            # Instead navigate the guide to find the channel position
            # This is fragile, if Frndly changes their default sort, or someone changes
            # the channel sort in settings this will break
            for i in range(guide_position):
                requests.post(device_url + down)
                time.sleep(0.5)
            requests.post(device_url + select)
            time.sleep(1)
            requests.post(device_url + select)  # Start selected channel

            time.sleep(2)
            set_active_app(device_url)

            time.sleep(2)
            set_default_display_msg()
    busy = False


# Get the active app ID
# Used to identify when to exit Netflix
def get_active_app(url):
    global busy

    active_channel = 0
    string_to_check = "oku"

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        app_state = primary_device_state
    else:
        app_state = secondary_device_state

    busy = True
    if app_state is "active":
        socket_available = retry_socket_connection(device_url)
        if socket_available is True:
            print("get_active_app: Attempting to get active channel for device", device_url)
            channel = requests.get(device_url + active_app)
            if channel is not None:
                channel_text = channel.text
                regex = re.compile("[\r\n]")
                parsed_response = regex.split(channel_text)
                if string_to_check not in parsed_response[2]:
                    regex = re.compile("[\"]")
                    tmp_channel = (regex.split(parsed_response[2]))
                    active_channel = int(tmp_channel[1])
                else:
                    print("get_active_app: attempt to get active channel failed for a different reason", channel_text)
            else:
                print("get_active_app: failed to get response from device for active channel")
    busy = False

    return active_channel


# Due to the polling of 15 minutes we need to set the active app
# This way a user can change the channel and not run into issues
# before the next polling
def set_active_app(url):
    global primary_active_app, secondary_active_app, busy

    if url:
        device_url = url
    else:
        device_url = url_1

    busy = True
    app_to_set = get_active_app(device_url)
    busy = False

    if device_url is url_1:
        primary_active_app = app_to_set
        print("set_active_app: primary active app is now", primary_active_app)
    else:
        secondary_active_app = app_to_set
        print("set_active_app: secondary active app is now", secondary_active_app)


# Query the devices to determine if they are online
# The remote won't try to launch an app if the device
# cannot be pinged successfully
def get_device_state(url):
    global busy

    device_state = "inactive"
    socket_available = False
    max_response_time = 65535
    host_response = max_response_time

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        host_ip = host_1_ip
    else:
        host_ip = host_2_ip

    try:
        host_response = esp.ping(host_ip)
    except RuntimeError as r:
        print("get_device_state: something went wrong with host check", r)
        pass

    busy = True
    if host_response < max_response_time:
        socket_available = retry_socket_connection(device_url)

    if socket_available is True:
        print("get_device_state: querying", device_url, "for status")
        requests.get(device_url + query_media)
        device_state = "active"
    busy = False

    return device_state


# Netflix likes to save your data by asking "are you still watching"
# Since we don't worry about that on these devices, interacting
# with the TV periodically will prevent them from popping up
def interact_with_tv(url):
    global busy

    if url:
        device_url = url
    else:
        device_url = url_1

    busy = True
    socket_status = retry_socket_connection(device_url)

    if socket_status is True:
        print("interact_with_tv: Interacting with TV to avoid Netflix prompt")
        requests.post(device_url + up)
    busy = False


# Exit current running app and power down the Roku TV or put the Roku device into sleep mode
def power_off(url):
    global second_tv, busy

    if url:
        device_url = url
    else:
        device_url = url_1

    if device_url is url_1:
        state = primary_device_state
        app = primary_active_app
    else:
        state = secondary_device_state
        app = secondary_active_app

    busy = True
    if state is "active":
        # only run exit_netflix() if we are currently watching Netflix
        if app == netflix_channel_id:
            exit_netflix(device_url)

        # Return to home screen and then power off
        socket_status = retry_socket_connection(device_url)

        if socket_status is True:
            print("power_off: Exiting app, returning to home screen, powering off display")

            requests.post(device_url + home)
            requests.post(device_url + pwr_off)

            if second_tv is True:
                second_tv = False
            else:
                set_default_display_msg()

            time.sleep(5)
            set_active_app(device_url)
    busy = False


# --- Main ---
while True:
    # Set commands for when a key is pressed
    # Keys only interact with the primary TV
    if neokey[0]:
        launch_netflix(url_1)

    if neokey[1]:
        launch_paramount(url_1)

    if neokey[2]:
        launch_frndly(url_1)

    if neokey[3]:
        power_off(url_1)

    # Interact with television, while watching Netflix, uses update_delay
    # which is set in the data.py file
    # If we don't do this, Netflix will prompt "Are you still watching"
    if last_check is None or time.monotonic() > last_check + update_delay:
        if busy is True:
            while busy is True:
                print("Currently busy with other work, will retry in 2 seconds.")
                time.sleep(2)
        else:
            busy = True
            # Set loading display
            set_loading_display_msg()

            # Get current time
            now = update_time()

            # Get the state of the primary TV
            primary_device_state = get_device_state(url_1)
            print("primary device state is", primary_device_state)

            # Get the state of the secondary TV
            secondary_device_state = get_device_state(url_2)
            print("secondary device state is", secondary_device_state)

            # Get active app for primary TV
            if primary_device_state is "active":
                primary_active_app = get_active_app(url_1)
                print("primary device active app is", primary_active_app)

            # Get active app for secondary TV
            if secondary_device_state is "active":
                secondary_active_app = get_active_app(url_1)
                print("secondary device active app is", secondary_active_app)

            # Set the default menu of what to watch
            set_default_display_msg()
            print("Ready to begin handling devices")
            last_check = time.monotonic()
            busy = False

    # If either TV is on and Netflix is playing
    # Interact with the TV to avoid the "are you still watching message"
    # Also handle turning on/off each device daily
    if interact_check is None or time.monotonic() > interact_check + interact_delay:
        now = cur_time

        if now is []:
            print("cur_time not set, need to get value")
            now = update_time()

        if busy is True:
            while busy is True:
                print("another process in progress, will retry in 2 seconds")
                time.sleep(2)
        else:
            busy = True
            if primary_device_state is "active":
                if primary_active_app == netflix_channel_id:
                    interact_with_tv(url_1)

            if secondary_device_state is "active":
                if secondary_active_app == netflix_channel_id:
                    interact_with_tv(url_2)
            busy = False

            # Turn on the primary TV each morning
            if now[3] == primary_tv_start_time[0] and now[4] >= primary_tv_start_time[1]:
                launch_netflix(url_1)

            # Turn off the primary TV each night
            if now[3] == primary_tv_end_time[0] and now[4] >= primary_tv_end_time[1]:
                power_off(url_1)

            # Turn on the secondary TV each evening
            if now[3] == secondary_tv_start_time[0] and now[4] >= secondary_tv_start_time[1]:
                second_tv = True
                launch_netflix(url_2)

            if now[3] == secondary_tv_end_time[0] and now[4] >= secondary_tv_end_time[1]:
                power_off(url_2)

            interact_check = time.monotonic()

    # A small test aid. This will set the pin value at random and launch the corresponding show
    # Unfortunately I was unable to force a key press
    # So this was the next best thing
    if test_mode is True and last_test_check is not None and time.monotonic() > last_test_check + test_delay:
        counter = 0
        while counter <= 4:
            print("TEST: on iteration", counter)
            neokey_key = random.choice([0, 1, 2, 3])
            if neokey_key == 0:
                print("testing key", neokey_key)
                neokey.digital_write(neokey_key, launch_netflix(url_1))
                time.sleep(2)
                neokey.digital_write(neokey_key)
            elif neokey_key == 1:
                print("testing key", neokey_key)
                neokey.digital_write(neokey_key, launch_paramount(url_1))
                time.sleep(2)
                neokey.digital_write(neokey_key)
            elif neokey_key == 2:
                print("testing key", neokey_key)
                neokey.digital_write(neokey_key, launch_frndly(url_1))
                time.sleep(2)
                neokey.digital_write(neokey_key)
            elif neokey_key == 3:
                print("testing key", neokey_key)
                neokey.digital_write(neokey_key, power_off(url_1))
                time.sleep(2)
                neokey.digital_write(neokey_key)

            counter += 1
            if counter < 3:
                time.sleep(20)

    last_test_check = time.monotonic()

    time.sleep(0.05)
