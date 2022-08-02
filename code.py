# SPDX-License-Identifier: MIT

import time
import board
import displayio
import busio
import digitalio
import re
import adafruit_requests as requests
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_display_text.bitmap_label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_neokey.neokey1x4 import NeoKey1x4

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
DISPLAY_BITPLANES = 6
UPDATE_DELAY = 3600
FONT = bitmap_font.load_font("/fonts/RobotoMono-Regular-8.pcf")

# Get Wifi information from secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Get Streaming services and shows from data.py file
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
socket.set_interface(esp)
session = requests.Session(socket)

# Neokey 1x4 keyboard
i2c_bus = board.STEMMA_I2C()
neokey = NeoKey1x4(i2c_bus, addr=0x30)

# Get what we need from the data file
urls = data["device_urls"]
current_shows = data["shows"]
current_channels = data["channels"]
guide_position = data["frndly_guide_position"]
netflix_search_int = data["netflix_search_int"]

# If this is not the primary television, don't set the LED display
second_tv = False
device_1 = "inactive"
device_2 = "inactive"
last_check = None
now_time = None
display_array = []

# URLs
url_1 = urls[0]
url_2 = urls[1]
device_url = url_1 # default to first device

# Shows for each streaming service
show_1 = current_shows[0]
show_2 = current_shows[1]
show_3 = current_shows[2]

# Streaming channels
channel_1 = current_channels[0]
channel_2 = current_channels[1]
channel_3 = current_channels[2]

# Split longer titles into an array
# Need to shorten longer titles to fit Matrix
paramount_show_for_display = show_2.split()
frndly_show_for_display = show_3.split()

# --- Roku API Calls ---
# Home
home = ("keypress/home")
#  Right
right = ("keypress/right")
#  Left
left = ("keypress/left")
# Up
up = ("keypress/up")
#  Down
down = ("keypress/down")
# Back
back = ("keypress/back")
#  select
select = ("keypress/select")
#  volume up
vol_up = ("keypress/volumeup")
#  volume down
vol_down = ("keypress/volumedown")
#  power on
pwr_on = ("keypress/poweron")
#  power off
pwr_off = ("keypress/poweroff")
# Launch Netflix
netflix = ("launch/12")
# Launch Paramount+
paramount = ("launch/31440")
# Launch FrndlyTV
frndly = ("launch/298229")
# Query Active Application
active_app = ("query/active-app")
# Query Device State
query_media = ("query/media-player")

# --- Display ---
matrix = Matrix()
display = matrix.display

group = displayio.Group()
bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_BITPLANES)
color = displayio.Palette(5)
color[0] = 0x000000 # black background
color[1] = 0XFF0000 # red = Netflix
color[2] = 0x00FFFF # blue = Paramount+
color[3] = 0x008000 # green = Frndly
color[4] = 0xFFFFFF # white =  default color
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
group.append(tile_grid)
display.show(group)


# --- Helper Methods for the Display ---
# Update the time
def update_time():
    now = time.localtime()
    network.get_local_time() #Synchronize Board's clock to internet

# Set the default display when active
# Color coded by show/channel
def set_default_display_msg():
    global display_array

    clear_display()

    hello1 = Label(
        font = FONT,
        color = color[4],
        text = "{0}".format("What to Watch"))
    bbx, bby, bbwidth, bbh = hello1.bounding_box
    hello1.x = round(display.width / 2 - bbwidth / 2)
    hello1.y = 4

    hello2 = Label(
        font = FONT,
        color = color[1],
        text = "{0}".format(show_1))
    bbx2, bby2, bbwidth2, bbh2 = hello2.bounding_box
    hello2.x = round(display.width / 2 - bbwidth2 / 2)
    hello2.y = 11

    hello3 = Label(
        font = FONT,
        color = color[2],
        text = "{0}".format(paramount_show_for_display[2]))
    bbx3, bby3, bbwidth3, bbh3 = hello3.bounding_box
    hello3.x = round(display.width / 2 - bbwidth3 / 2)
    hello3.y = 18

    hello4 = Label(
        font = FONT,
        color = color[3],
        text = "{0}".format(frndly_show_for_display[0]))
    bbx4, bby4, bbwidth4, bbh4 = hello4.bounding_box
    hello4.x = round(display.width / 2 - bbwidth4 / 2)
    hello4.y = 25

    group.append(hello1)
    group.append(hello2)
    group.append(hello3)
    group.append(hello4)

    display_array = ["hello1", "hello2", "hello3", "hello4"]

# This method is called to update the display
# The display will read "Now Playing \r <selected show>"
def set_watching_display(channel=None):
    global display_array

    if channel:
        channel = channel

    # Set the second line of the display based on the channel chosen
    if channel is channel_1:
        show_text = "{0}".format(show_1)
        show_color = color[1]
    elif channel is channel_2:
        show_text = "{0}".format(paramount_show_for_display[2])
        show_color = color[2]
    elif channel is channel_3:
        show_text = "{0}".format(frndly_show_for_display[0])
        show_color = color[3]

    line1 = Label(
        font = FONT,
        color = color[4],
        text = "{0}".format("Now Playing"))
    bbx1, bby1, bbwidth1, bbh1 = line1.bounding_box
    line1.x = round(display.width / 2 - bbwidth1 / 2)
    line1.y = 8

    line2 = Label(
        font = FONT,
        color = show_color,
        text = show_text)
    bbx2, bby2, bbwidth2, bbh2 = line2.bounding_box
    line2.x = round(display.width / 2 - bbwidth2 /2)
    line2.y = 24

    clear_display()
    display_array = ["line1", "line2"]
    group.append(line1)
    group.append(line2)

# Clear the display based on msg_text
def clear_display():
    global display_array

    for i in range(len(display_array)):
        group.pop()

# --- Helper methods for other tasks not related to the Roku or Display ---
def get_show_search_array(show=None):
    if show is None:
        print ("No show to parse, please specify a show name")

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
# Perform a search.
# Using search as a more reliable way to find what to watch
def search_program(url=None, show=None, channel=None):
    global device_url, netflix_search_int

    if show is None:
        print("Please provide a show to use in search")

    if url:
        device_url = url

    if channel:
        channel = channel

    # If using Netflix, the search will remain on the last letter
    # of the searched show, so the amount we need to navigate to select
    # the show changes.
    # For ease of use I've stored this value in data.py
    channel_1_search_int = netflix_search_int
    channel_2_search_int = 6
    channel_3_search_int = 3

    if channel is channel_1:
        search_int = channel_1_search_int
    elif channel is channel_2:
        search_int = channel_2_search_int
    elif channel is channel_3:
        search_int = channel_3_search_int

    show_to_search = get_show_search_array(show)

    for i in show_to_search:
        session.post(device_url + "keypress/Lit_" + i)
        time.sleep(0.75)
    time.sleep(2)
    for x in range(search_int):
        session.post(device_url + right)
        time.sleep(0.5)
    session.post(device_url + select)
    time.sleep(1)

# Launch the Netflix app on target device
# Select the last used profile
# Bring up the left nav menu
# Execute search for chosen show and select
def launch_netflix(url=None):
    global device_url, second_tv, device_1, device_2

    if url:
        device_url = url

    print("launching ", show_1, " on ", channel_1, " on device ", device_url)

    if second_tv is False:
        set_watching_display(channel=channel_1)
    else:
        second_tv = False

    if device_url is url_1:
        if device_1 is "inactive":
            print("powering on device at ", url_1)
            device_1 = "active"
            power_on(url=url)
    elif device_url is url_2:
        if device_2 is "inactive":
            print("powering on device at ", url_2)
            device_2 = "active"
            power_on(url=url)
    else:
        print("device at ", device_url, " is active")

    session.post(device_url + netflix) # launch Netflix on the Roku Streambar
    time.sleep(5)
    session.post(device_url + select) # select the active profile
    time.sleep(5)
    session.post(device_url + left) # open the left nav menu
    time.sleep(1)
    session.post(device_url + up) # navigate to search
    time.sleep(1)
    session.post(device_url + select) # enter search
    time.sleep(1)
    session.post(device_url + left) # Move from Top Searchs to the search box
    time.sleep(1)
    search_program(url=device_url, show=show_1, channel=channel_1)
    time.sleep(1)
    session.post(device_url + select) # Star the selected show

# Because Netflix never leaves you in a known state
# we need to exit the app every time we turn off the TV or change apps
def exit_netflix(url=None):
    global device_url

    if url:
        device_url = url

    print("exiting ", channel_1)

    for x in range(4): # Get back to left nav
        session.post(device_url + back)
        time.sleep(1)
    session.post(device_url + down) # Navigate to home, our start point
    time.sleep(0.25)
    session.post(device_url + select) # Select it to save it
    time.sleep(0.5)
    session.post(device_url + back) # Return to left nav
    time.sleep(0.25)
    for i in range(2): # Move up to the profile
        session.post(device_url + up)
        time.sleep(0.5)
    session.post(device_url + select) # Select it to land on profiles page

# Launch Paramount+
# Choose second profile
# Open left nav
# Move to search
# Execute search for show and select
def launch_paramount(url=None):
    global device_url, second_tv, device_1, device_2

    if url:
        device_url = url

    # check and see if Netflix is active, if so exit the app before starting new show
    active_channel = get_active_app(url=url)
    if active_channel is "12":
        exit_netflix(url=device_url)

    print("launching ", show_2, "on ", channel_2, " on device ", device_url)

    # Set the display to indicate what we're watching
    if second_tv is False:
        set_watching_display(channel=channel_2)
    else:
        second_tv = False

    if device_url is url_1:
        if device_1 is "inactive":
            print("powering on device at ", url_1)
            device_1 = "active"
            power_on(url=device_url)
    elif device_url is url_2:
        if device_2 is "inactive":
            print("powering on device at ", url_2)
            device_2 = "active"
            power_on(url=device_url)
    else:
        print("device at ", device_url, " is active")

    session.post(device_url + paramount) # launch Paramount+
    time.sleep(10)
    session.post(device_url + right) # Navigate to second profile
    time.sleep(2)
    session.post(device_url + select) # Select second profile
    time.sleep(6)
    session.post(device_url + left) # Access lef nav
    time.sleep(0.5)
    session.post(device_url + up) # Move up to enter Search
    time.sleep(0.5)
    session.post(device_url + select) # Enter Search
    time.sleep(0.5)
    search_program(url=device_url, show=show_2, channel=channel_2)
    time.sleep(0.5)
    session.post(device_url + select) # Select the searched show
    time.sleep(2)
    session.post(device_url + select) # Start playing the show

# Launch FrndlyTV
# Navigate to the selected channel in the guide
# Select that channel
# Select Watch Live
def launch_frndly(url=None):
    global device_url, guide_position, second_tv, device_1, device_2

    if url:
        device_url = url

    # check and see if Netflix is active, if so exit the app before starting new show
    active_channel = get_active_app(url=url)
    if active_channel is "12":
        exit_netflix(url=device_url)

    print("launching ", show_3, " on ", channel_3, " on device ", device_url)

    if second_tv is False:
        set_watching_display(channel=channel_3)
    else:
        second_tv = False;

    if device_url is url_1:
        if device_1 is "inactive":
            print("powering on device at ", url_1)
            device_1 = "active"
            power_on(url=device_url)
    elif device_url is url_2:
        if device_2 is "inactive":
            print("powering on device at ", url_2)
            device_2 = "active"
            power_on(url=device_url)
    else:
        print("device at ", device_url, " is active")

    session.post(device_url + frndly) # Launch FrndlyTV
    time.sleep(10)
    # Since FrndlyTV search is non-standard, we can't search without it
    # being clunky and downright ugly
    # Instead navigate the guide to find the channel position
    # This is fragile, if Frndly changes their default sort, or someone changes
    # the channel sort in settings this will break
    for i in range(guide_position):
        session.post(device_url + down)
        time.sleep(0.5)
    session.post(device_url + select)
    time.sleep(1)
    session.post(device_url + select) # Start selected channel

# This query will return the active app (name and ID) from the device
# Currently used to determine if we need to run exit_netflix()
def get_active_app(url=None):
    global device_url

    if url:
        device_url = url

    string_to_check = "oku"

    channel = session.get(device_url + active_app)
    channel_text = channel.text
    regex = re.compile("[\r\n]")
    parsed_response = regex.split(channel_text)
    # We do this because this is the one response that doesn't return an app_id
    if string_to_check in parsed_response[2]:
        active_channel = "Roku"
        return active_channel
    else:
        regex = re.compile("[\"]")
        active_channel = (regex.split(parsed_response[2]))
        return active_channel[1]

def get_device_state(url=None):
    global device_url

    if url:
        device_url = url

    # need to check t see if the device is active or stopped
    string_to_check = ["stop", "close"]
    device_status = session.get(device_url + query_media)
    device_status_text = device_status.text

    regex = re.compile("[\r\n]")
    device_state_to_parse = regex.split(device_status_text)
    regex = re.compile("[\"]")
    line_to_search = (regex.split(device_state_to_parse[1]))

    for word in (string_to_check):
        search_string = word
        if search_string is line_to_search[3]:
            device_state = "inactive"
            break
        else:
            device_state = "active"

    return device_state

def interact_with_tv(url=None):
    global device_url

    if url:
        device_url = url

    is_netflix = get_active_app(device_url)

    if is_netflix is "12":
        print("interacting with TV to avoid Netflix prompt")
        session.post(device_url + vol_down)
        time.sleep(0.25)
        session.post(device_url + vol_up)

def power_on(url=None):
    global device_url

    if url:
        device_url = url

    session.post(device_url + pwr_on) # turn Roku TV on
    time.sleep(10)

# Exit current running app and power down the Roku TV or put the Roku device into sleep mode
def power_off(url=None):
    global device_url, device_1, device_2

    if url:
        device_url = url

    current_app = get_active_app(url=url)

    # only run exit_netflix() if we are currently watching Netflix
    if current_app is "12":
        exit_netflix(url=device_url)

    # Return to home screen and then power off
    print("Returning to home screen and powering down")
    session.post(device_url + home)
    session.post(device_url + pwr_off)

    if second_tv is False:
        set_default_display_msg()

    if device_url is url_1:
        device_1 = "inactive"
    elif device_url is url_2:
        device_2 = "inactive"

# --- Start Up ---
# Set the default text
set_default_display_msg()

# Sate that drives whether we turn on the second TV
second_tv_running = True # Change me!!!

# --- Main ---
while True:

    # Keyboard handling
    # All commands go to the primary TV
    # Set colors for the keys
    neokey.pixels[0] = color[1]
    neokey.pixels[1] = color[2]
    neokey.pixels[2] = color[3]
    neokey.pixels[3] = color[4]
    # Set commands for when key is pressed
    if neokey[0]:
        launch_netflix(url=url_1)

    if neokey[1]:
        launch_paramount(url=url_1)

    if neokey[2]:
        launch_frndly(url=url_1)

    if neokey[3]:
        power_off(url=url_1)

    # Interact with television, while watching Netflix, every hour
    # If we don't do this, Netflix will prompt "Are you still watching"
    if last_check is None or time.monotonic() > last_check + UPDATE_DELAY:
        try:
            update_time()
            now = time.localtime(time.time())

            # Get device state for all devices
            url_1_state = get_device_state(url=url_1)
            url_2_state = get_device_state(url=url_2)

            # If either device is active
            # Interact with the TV if Netflix is running
            if url_1_state is "active":
                interact_with_tv(url=url_1)
                device_1 = "active"

            if url_2_state is "active":
                interact_with_tv(url=url_2)
                device_2 = "active"

            # Set up the second TV for the evening
            if second_tv_running is False and now[3] == 19 and now[4] >= 30:
                second_tv = true
                launch_netflix(url=url_2)
                second_tv_running = True
            else:
                print ("second TV already running")

            # Turn off the second TV
            if (now[3] == 21 and now[4] >= 30):
                if url_2 is "active":
                    power_off(url=url_2)
                    second_tv_running = True #Change me!

            # Turn off the primary TV
            if (now[3] == 20 and now[4] == 45):
                if url_1 is "active":
                    power_off(url=url_1)

            last_check = time.monotonic()
        except RuntimeError as e:
            print("An error occured, retrying ... ", e)
