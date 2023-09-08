# SPDX-License-Identifier: MIT

# This is a very simple remote, designed for individuals with difficulty navigating
# all the different streaming applications
# It was designed to help a senior have less frustration while trying to watch television

import time
import random
import board
import busio
import digitalio
import re
import displayio
import microcontroller
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_neokey.neokey1x4 import NeoKey1x4
from adafruit_matrixportal.network import Network

FONT = "/fonts/RedHatMono-Medium-8.bdf"

# Get WiFi information from secrets.py file
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
socket.set_interface(esp)
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
primary_tv_channel = data["primary_tv_channel"]
secondary_tv_start_time = data["secondary_tv_start_time"]
secondary_tv_end_time = data["secondary_tv_end_time"]
secondary_tv_channel = data["secondary_tv_channel"]
update_delay = data["update_delay"]
interact_delay = data["interact_delay"]
remote_reboot_time = data["remote_reboot_time"]
primary_reboot = True
secondary_reboot = True

# Setting necessary defaults
second_tv = False
default_display = False
busy = False
last_check = None
interact_check = None
display_array = []
primary_device_state = None
secondary_device_state = None
primary_active_app = None
secondary_active_app = None
primary_channel_name = None
secondary_channel_name = None
primary_show_name = None
secondary_show_name = None


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

first_channel_id = int(channel_id_1)
second_channel_id = int(channel_id_2)
third_channel_id = int(channel_id_3)

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
# matrix = Matrix()
# display = matrix.display

matrix = MatrixPortal(esp=esp)

color = displayio.Palette(7)
color[0] = 0x000000  # black background
color[1] = 0XFF0000  # red = Show 1
color[2] = 0x00FFFF  # blue = Show 2
color[3] = 0x008000  # green = Show 3
color[4] = 0xFFFFFF  # white =  default color
color[5] = 0xFF4500  # orange/red
color[6] = 0x8B008B  # magenta

# --- Set up the keyboard ---
i2c_bus = board.STEMMA_I2C()
neokey = NeoKey1x4(i2c_bus, addr=0x30)
neokey_2 = NeoKey1x4(i2c_bus, addr=0x31)

# Set colors for the keyboard
neokey.pixels[0] = color[1]
neokey.pixels[1] = color[2]
neokey.pixels[2] = color[3]
neokey.pixels[3] = color[4]

# Set colors for second keyboard
neokey_2.pixels[1] = color[5]
neokey_2.pixels[2] = color[6]


# --- Helper Methods for the Display ---

# Update the time, synchronize board clock, and return current time
def get_time(sync):
    cur_time = None

    while cur_time is None:
        try:
            cur_time = time.localtime()
        except RuntimeError as e:
            print("get_time: An error occurred, retrying ... ", e)
            continue

    if sync is True:
        synchronize_clock()

    return cur_time


def synchronize_clock():
    tick_tock = 0

    while tick_tock <= 2:
        try:
            network.get_local_time()  # Synchronize Board's clock to internet
            tick_tock = 3
        except RuntimeError as r:
            print("synchronize_clock: unable to synchronize board clock to internet. Error:", r, "attempt", tick_tock,
                  "of 3, will retry in 2 seconds")
            continue

        tick_tock += 1
        time.sleep(2)


# Set loading display message
# Used during initial start and each recheck
def set_loading_display_msg():
    global display_array, default_display

    matrix.remove_all_text(True)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12) + 10,
            (matrix.graphics.display.height // 2) - 12,
        ),
        text_color=color[4],
    )

    matrix.set_text_color(color[4], 0)
    matrix.set_text("LOADING", 0)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12),
            (matrix.graphics.display.height // 2 + 2),
        ),
        text_color=color[4],
    )
    matrix.set_text_color(color[4], 1)
    matrix.set_text("PLEASE WAIT", 1)

    default_display = False


def set_secondary_tv_start_msg():
    global display_array, default_display

    matrix.remove_all_text(True)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12 + 4),
            (matrix.graphics.display.height // 2) - 12,
        ),
        text_color=color[4],
    )
    matrix.set_text_color(color[4], 0)
    matrix.set_text("BEDROOM TV", 0)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12 + 8),
            (matrix.graphics.display.height // 2) + 2,
        ),
    )
    matrix.set_text_color(color[4], 1)
    matrix.set_text("STARTING", 1)

    default_display = False


# Set the default display when active
# Color coded by show/channel
def set_default_display_msg():
    global display_array, default_display

    if default_display is False:
        matrix.remove_all_text(True)
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12) + 4,
                (matrix.graphics.display.height // 2) - 12,
            ),
            text_color=color[1],
        )
        matrix.set_text_color(color[1], 0)
        matrix.set_text(show_1, 0)

        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 - 4),
                (matrix.graphics.display.height // 2 - 3),
            ),
            text_color=color[2],
        )
        matrix.set_text_color(color[2], 1)
        matrix.set_text(show_2, 1)

        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 + 6),
                (matrix.graphics.display.height // 2 + 3),
            ),
            text_color=color[3],
        )
        matrix.set_text_color(color[3], 2)
        matrix.set_text(show_3, 2)

        default_display = True


# Set the display while launching a show
# The display will read "Now Playing \r <selected show>"
def set_watching_display(channel, show):
    global default_display

    show_color = color[4]  # default show color

    matrix.remove_all_text(True)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12),
            (matrix.graphics.display.height // 2) - 12,
        ),
        text_color=color[4],
    )
    matrix.set_text_color(color[4], 0)
    matrix.set_text("NOW PLAYING", 0)

    if channel is channel_1:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12) + 2,
                (matrix.graphics.display.height // 2 - 2),
            ),
            text_color=show_color,
        )
        matrix.set_text_color(color[1], 1)
        matrix.set_text(show, 1)
    elif channel is channel_2:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 - 4),
                (matrix.graphics.display.height // 2) + 2,
            ),
            text_color=show_color,
        )
        matrix.set_text_color(color[2], 1)
        matrix.set_text(show, 1)
    elif channel is channel_3:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 + 6),
                (matrix.graphics.display.height // 2) + 2,
            ),
            text_color=show_color,
        )
        matrix.set_text_color(color[3], 1)
        matrix.set_text(show, 1)

    default_display = False


def set_volume_change_msg(direction):
    global default_display

    matrix.remove_all_text(True)

    if direction == "up":
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 + 4),
                (matrix.graphics.display.height // 2),
            ),
            text_color=color[5],
        )

        matrix.set_text("SOUND UP", 0)
    else:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12),
                (matrix.graphics.display.height // 2),
            ),
            text_color=color[6],
        )
        matrix.set_text("SOUND DOWN", 0)

    default_display = False
    time.sleep(1)


def set_exit_show_msg(show):
    global default_display

    print("show is", show)

    if show is show_1:
        show_color = color[1]
    elif show is show_2:
        show_color = color[2]
    elif show is show_3:
        show_color = color[3]
    else:
        show_color = color[4]

    matrix.remove_all_text(True)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12) + 10,
            (matrix.graphics.display.height // 2) - 12,
        ),
        text_color=color[4],
    )
    matrix.set_text("EXITING", 0)

    if show is show_1:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12) + 2,
                (matrix.graphics.display.height // 2 - 2),
            ),
            text_color=show_color,
        )
        matrix.set_text(show, 1)
    elif show is show_2:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 - 4),
                (matrix.graphics.display.height // 2) - 2,
            ),
            text_color=show_color,
        )
        matrix.set_text(show, 1)
    elif show is show_3:
        matrix.add_text(
            text_font=FONT,
            text_position=(
                (matrix.graphics.display.width // 12 + 6),
                (matrix.graphics.display.height // 2) + 2,
            ),
            text_color=show_color,
        )
        matrix.set_text(show, 1)

    default_display = False


def set_power_off_msg():
    global default_display

    matrix.remove_all_text(True)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12) + 10,
            (matrix.graphics.display.height // 2) - 12,
        ),
        text_color=color[4],
    )
    matrix.set_text("POWER OFF", 0)

    matrix.add_text(
        text_font=FONT,
        text_position=(
            (matrix.graphics.display.width // 12) + 10,
            (matrix.graphics.display.height // 2) + 2,
        ),
        text_color=color[4],
    )
    matrix.set_text("GOODBYE", 1)

    default_display = False


# --- Helper methods for other tasks not related to the Roku or Display ---


# Convert a show name to an array for searching
def get_show_search_array(show):
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


def get_channel_id(channel):
    if channel is channel_1:
        channel_id = channel_id_1
    elif channel is channel_2:
        channel_id = channel_id_2
    elif channel is channel_3:
        channel_id = channel_id_3
    else:
        channel_id = None

    return channel_id


def set_channel_and_show(url, app):
    global primary_channel_name, secondary_channel_name, primary_show_name, secondary_show_name

    print("app is", app)

    for i in range(len(current_channels)):
        if app == first_channel_id:
            if url is url_1:
                primary_channel_name = channel_1
                primary_show_name = show_1
            else:
                secondary_channel_name = channel_1
                secondary_show_name = show_1
        elif app == second_channel_id:
            if url is url_1:
                primary_channel_name = channel_2
                primary_show_name = show_2
            else:
                secondary_channel_name = channel_2
                secondary_show_name = show_2
        elif app == third_channel_id:
            if url is url_1:
                primary_channel_name = channel_3
                primary_show_name = show_3
            else:
                secondary_channel_name = channel_3
                secondary_show_name = show_3


#  --- Helper methods for interacting with Roku ---
# After a while an OutOfRetries
# Have each method call this prior to making the actual call to the device
def send_request(url, command):
    global busy

    result = None
    loop = True
    counter = 0

    while loop is True:
        if busy is True:
            print("busy doing other work, will retry in 2 seconds")
        else:
            while counter <= 2:
                busy = True
                if counter > 0:
                    print("trying query again, attempt", counter, "for command", command)
                try:
                    if "active-app" in command:
                        print("querying for active app")
                        response = requests.get(url + command)
                        result = response.text
                        response.close()
                        counter = 3
                        loop = False
                    elif "media-player" in command:
                        print("querying media player")
                        response = requests.get(url + command)
                        result = response.text
                        response.close()
                        counter = 3
                        loop = False
                    else:
                        response = requests.post(url + command)
                        result = "true"
                        response.close()
                        counter = 3
                        loop = False
                except Exception as e:
                    print("send_request: Caught generic exception", e, "for command", command)
                    if counter > 2:
                        print("unable to complete request")
                        pass
                    else:
                        counter += 1
                    time.sleep(2)

                busy = False
                esp.socket_close(0)

    return result


# Use in-channel search to locate show to watch
# Using search as a more reliable way to find what to watch
def search_program(url, channel, show):
    if url:
        device_url = url
    else:
        device_url = url_1

    # If using Netflix, the search will remain on the last letter
    # of the searched show, so the amount we need to navigate to select
    # the show changes.
    # For ease of use I've stored this value in data.py
    if channel is "Netflix":
        search_int = netflix_search_int
    elif channel is "Paramount":
        search_int = paramount_search_int
    else:
        search_int = 0

    for i in show:
        command = ("keypress/Lit_" + i)
        send_request(device_url, command)
        time.sleep(0.5)

    time.sleep(1)

    for x in range(search_int):
        send_request(device_url, right)
        time.sleep(0.5)

    if channel is not "PlutoTV":
        send_request(device_url, select)
    time.sleep(1)


# Launch the Netflix app on target device
# Select the last used profile
# Bring up the left nav menu
# Execute search for chosen show and select
def launch_netflix(url):
    global second_tv

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

        if app not in [int(channel_id_1), int(channel_id_2), int(channel_id_3)]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check and see if Netflix is active, if so exit the app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit the app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        set_channel_and_show(device_url, 12)

        if device_url is url_1:
            channel = primary_channel_name
            show = primary_show_name
        else:
            channel = secondary_channel_name
            show = secondary_show_name

        channel_id = get_channel_id(channel)

        print("launching", show, "on", channel, "on device", device_url)

        if second_tv is True:
            second_tv = False
        else:
            set_watching_display(channel, show)

        channel_call = (launch + channel_id)

        send_request(device_url, channel_call)  # launch Netflix
        time.sleep(15)
        send_request(device_url, select)  # select the active profile
        time.sleep(2)
        send_request(device_url, left)  # open the left nav menu
        time.sleep(1)
        for nav in range(5):  # Navigate to My List
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, select)  # enter search
        time.sleep(1)
        send_request(device_url, select)  # Star the selected show
        time.sleep(1)
        send_request(device_url, select)  # Star the selected show

        time.sleep(2)
        set_active_app(device_url)

        time.sleep(2)
        set_default_display_msg()


def wake_up_netflix(url):
    print("checking to see if I need to wake up netflix to proceed")
    if url is url_1:
        device_url = url_1
    else:
        device_url = url_2

    show_status = send_request(device_url, query_media)
    if primary_active_app == 12:
        if "pause" in show_status:
            print("")
        else:
            print("show playing, need to wake it up")
            send_request(device_url, back)
            time.sleep(1)


# Because Netflix never leaves you in a known state
# we need to exit the app every time we turn off the TV or change apps
def exit_netflix(url):
    if url:
        device_url = url
    else:
        device_url = url_1

    if primary_show_name is None and secondary_show_name is None:
        set_channel_and_show(device_url, 12)

    if device_url is url_1:
        channel = primary_channel_name
        show = primary_show_name
    else:
        channel = secondary_channel_name
        show = secondary_show_name

    return_range = 3

    set_exit_show_msg(show)

    print("exiting ", channel)
    for x in range(return_range):  # Get back to left nav
        send_request(device_url, back)
        time.sleep(1)
    for nav in range(5):
        send_request(device_url, up)
        time.sleep(1)
    send_request(device_url, select)  # Return to home screent
    time.sleep(1)
    send_request(device_url, left)  # Return to left nav
    time.sleep(1)
    for i in range(4):  # Move up to the profile
        send_request(device_url, up)
        time.sleep(1)
    send_request(device_url, select)  # Select it to land on profiles page
    time.sleep(1)
    send_request(device_url, home)


# Launch Pluto TV
# Set up is different.
# This method assumes the show you want to watch
# is in your continue watching list
def launch_pluto(url):
    global second_tv

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

    if state is "active":
        if app not in [int(channel_id_1), int(channel_id_2), int(channel_id_3)]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check to see if Netflix is active, if so exit app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        set_channel_and_show(device_url, 74519)

        if device_url is url_1:
            channel = primary_channel_name
            show = primary_show_name
        else:
            channel = secondary_channel_name
            show = secondary_show_name

        channel_id = get_channel_id(channel)

        print("launching ", show, "on ", channel, " on device ", device_url)

        # Set the display to indicate what we're watching
        if second_tv is True:
            second_tv = False
        else:
            set_watching_display(channel, show)

        channel_call = (launch + channel_id)

        wait_for_start = True

        send_request(device_url, channel_call)  # launch Pluto TV

        while wait_for_start is True:
            # Use this line if watching on a Roku TV
            # if "<is_live blocked=\"false\">true</is_live>" in send_request(url, query_media):
            # Use this line if watching on a Roku Device (Premier, Streambar)
            if "<is_live>true</is_live>" in send_request(url, query_media):
                wait_for_start = False
                print("station loaded, ready to proceed")
            else:
                print("waiting for channel to launch")
                time.sleep(4)
        print("start launch procedure")

        send_request(device_url, left)  # Open left nav
        time.sleep(1)
        for i in range(2):
            send_request(device_url, down)  # Navigate to On Demand
            time.sleep(1)
        send_request(device_url, select)  # Select On Demand
        time.sleep(1)
        for i in range(2):
            send_request(device_url, down)  # Navigate to On Demand
            time.sleep(2)
        send_request(device_url, right)
        time.sleep(1)
        send_request(device_url, select)
        time.sleep(1)
        send_request(device_url, select)
        time.sleep(5)
        confirm_pluto_show_loaded(device_url)

        time.sleep(2)
        set_active_app(device_url)

        time.sleep(2)
        set_default_display_msg()


#
# Pluto can be a bit contrary at times
# Check that it actually loaded the program we want
#

def confirm_pluto_show_loaded(url):
    show_launched = False

    if url:
        device_url = url
    else:
        device_url = url_1

    print("confirming chosen PlutoTV show has launched")
    while show_launched is False:

        # Use this if watching on a Roku TV
        # if "<is_live blocked=\"false\">true</is_live>" in send_request(url, query_media):
        # Use this if watching on a Roku device (Premier, Streambar)
        if "<is_live>true</is_live>" in send_request(device_url, query_media):
            print("Didn't launch chosen show, trying again")
            launch_channel(device_url, 74519)
        else:
            print("Chosen show successfully launched")
            show_launched = True

        time.sleep(2)


# Similar to Netflix
# We need to exit Pluto to ensure a known starting point
def exit_pluto(url):
    if url:
        device_url = url
    else:
        device_url = url_1

    if primary_show_name is None and secondary_show_name is None:
        set_channel_and_show(device_url, 74519)

    if device_url is url_1:
        show = primary_show_name
        channel = primary_channel_name
    else:
        show = secondary_show_name
        channel = secondary_channel_name

    media_player_status = send_request(url, query_media)

    # Use this if watching on a Roku TV
    # if "<is_live blocked=\"false\">true</is_live>" in send_request(url, query_media):
    # Use this if watching on a Roku device (Premier, Streambar)
    if "<is_live>true</is_live>" in media_player_status:
        return_range = 4
    else:
        return_range = 5

    print("exiting ", channel)
    set_exit_show_msg(show)
    for x in range(return_range):  # Exit App
        send_request(device_url, back)
        time.sleep(2)
    send_request(device_url, down)  # Navigate to Exit App in selection
    time.sleep(1)
    send_request(device_url, select)  # Exit app, return to home screen


# Launch Selected Channel on YouTube TV
def launch_youtubetv(url):
    global second_tv

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

    if state is "active":
        if app not in [int(channel_id_1), int(channel_id_2), int(channel_id_3)]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check to see if Netflix is active, if so exit app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        set_channel_and_show(device_url, 195316)

        if device_url is url_1:
            channel = primary_channel_name
            show = primary_show_name
        else:
            channel = secondary_channel_name
            show = secondary_show_name

        channel_id = get_channel_id(channel)

        print("launching ", show, "on ", channel, " on device ", device_url)

        # Set the display to indicate what we're watching
        if second_tv is True:
            second_tv = False
        else:
            set_watching_display(channel, show)

        channel_call = (launch + channel_id)

        send_request(device_url, channel_call)  # launch YouTube TV
        time.sleep(15)
        for i in range(2):
            send_request(device_url, right)  # Navigate to search
            time.sleep(1)
        send_request(device_url, down)  # Enter search
        time.sleep(1)
        search_program(device_url, channel, show)  # Search for channel
        time.sleep(1)
        for i in range(1):
            send_request(device_url, right)  # Navigate to searched channel
            time.sleep(2)
        send_request(device_url, select)
        time.sleep(1)
        send_request(device_url, down)
        time.sleep(1)
        for i in range(1):
            send_request(device_url, select)
            time.sleep(1)
        time.sleep(1)
        set_active_app(device_url)

        time.sleep(2)
        set_default_display_msg()


# Launch Paramount+
# Choose second profile
# Open left nav
# Move to search
# Execute search for show and select
def launch_paramount(url):
    global second_tv

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

    if state is "active":
        if app not in [first_channel_id, second_channel_id, third_channel_id]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check to see if Netflix is active, if so exit the app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit the app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)
        # See if we're in Paramount or Frndly
        if app == 31440 or app == 298229:
            send_request(device_url, home)

        set_channel_and_show(device_url, 31440)

        if device_url is url_1:
            show = primary_show_name
            channel = primary_channel_name
        else:
            show = secondary_show_name
            channel = secondary_channel_name

        channel_id = get_channel_id(channel)

        print("launching ", show, "on ", channel, " on device ", device_url)

        # Set the display to indicate what we're watching
        if second_tv is True:
            second_tv = False
        else:
            set_watching_display(channel, show)

        channel_call = (launch + channel_id)

        send_request(device_url, channel_call)  # launch Paramount+
        time.sleep(10)
        send_request(device_url, right)  # Navigate to second profile
        time.sleep(2)
        send_request(device_url, select)  # Select second profile
        time.sleep(5)
        send_request(device_url, left)  # Access lef nav
        time.sleep(1)
        for i in range(7):
            send_request(device_url, down)  # Move Down to My List
            time.sleep(1)
        send_request(device_url, select)  # Select My List
        time.sleep(2)
        send_request(device_url, select)  # Select the first show in the list
        time.sleep(2)
        send_request(device_url, select)  # Start playing the show

        time.sleep(2)
        set_active_app(device_url)

        time.sleep(2)
        set_default_display_msg()


# Launch FrndlyTV
# Navigate to the selected channel in the guide
# Select that channel
# Select Watch Live
def launch_frndly(url):
    global second_tv

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

    if state is "active":
        if app not in [first_channel_id, second_channel_id, third_channel_id]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check to see if Netflix is active, if so exit the app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit the app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        # Check if we're already watching Frndly, then exit.
        if app == 298229:
            send_request(url, home)
            time.sleep(1)

        set_channel_and_show(device_url, 298229)

        if device_url is url_1:
            show = primary_show_name
            channel = primary_channel_name
        else:
            show = secondary_show_name
            channel = secondary_channel_name

        channel_id = get_channel_id(channel)

        print("launching ", show, " on ", channel, " on device ", device_url)

        if second_tv is True:
            second_tv = False
        else:
            set_watching_display(channel, show)

        channel_call = (launch + channel_id)

        send_request(device_url, channel_call)  # Launch FrndlyTV
        time.sleep(10)
        # Since FrndlyTV search is non-standard, we can't search without it
        # being clunky and downright ugly
        # Instead navigate the guide to find the channel position
        # This is fragile, if Frndly changes their default sort, or someone changes
        # the channel sort in settings this will break
        for i in range(guide_position):
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, select)
        time.sleep(1)
        send_request(device_url, select)  # Start selected channel

        time.sleep(2)
        set_active_app(device_url)

        time.sleep(2)
        set_default_display_msg()


# Get the active app ID
# Used to identify when to exit Netflix
def get_active_app(url):
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

    if app_state is "active":
        print("get_active_app: Attempting to get active channel for device", device_url)
        channel_text = send_request(device_url, active_app)
        print("data returned is", channel_text)
        if channel_text is not None:
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

    return active_channel


# Due to the polling of 15 minutes we need to set the active app
# This way a user can change the channel and not run into issues
# before the next polling
def set_active_app(url):
    global primary_active_app, secondary_active_app

    if url:
        device_url = url
    else:
        device_url = url_1

    app_to_set = get_active_app(device_url)

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
    device_state = "inactive"
    max_response_time = 65535
    host_response = max_response_time + 100

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

    if host_response < max_response_time:
        print("get_device_state: querying", device_url, "for status")
        if send_request(device_url, query_media) is not None:
            device_state = "active"

    return device_state


# Netflix likes to save your data by asking "are you still watching"
# Since we don't worry about that on these devices, interacting
# with the TV periodically will prevent them from popping up
def interact_with_tv(url):
    if url:
        device_url = url
    else:
        device_url = url_1

    netflix_show_status = send_request(device_url, query_media)
    if "pause" in netflix_show_status or "stop" in netflix_show_status:
        print("")
    else:
        print("interact_with_tv: Interacting with TV to avoid Netflix prompt")
        send_request(device_url, up)
        time.sleep(1)


# Exit current running app and power down the Roku TV or put the Roku device into sleep mode
def power_off(url):
    global second_tv

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

    if state is "active":

        # Check to see if Netflix is active, is so exit the app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Netflix is active, is so exit the app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        set_power_off_msg()

        print("power_off: Exiting app, returning to home screen, powering off display")

        send_request(device_url, home)
        time.sleep(10)
        set_active_app(device_url)
        time.sleep(5)
        send_request(device_url, pwr_off)

        if second_tv is True:
            second_tv = False
        else:
            set_default_display_msg()


def volume_up(url):
    if url:
        device_url = url
    else:
        device_url = url_1

    set_volume_change_msg("up")
    send_request(device_url, vol_up)
    time.sleep(0.25)
    set_default_display_msg()


def volume_down(url):
    if url:
        device_url = url
    else:
        device_url = url_1

    set_volume_change_msg("down")
    send_request(device_url, vol_down)
    time.sleep(0.25)
    set_default_display_msg()


def launch_channel(url, app):

    print("app provided is", app)

    if app == 12:
        print("launching show on netflix")
        launch_netflix(url)
    if app == 74519:
        print("launching show on pluto")
        launch_pluto(url)
    if app == 31440:
        print("launching show on paramount")
        launch_paramount(url)
    if app == 298229:
        print("launching show on frndly")
        launch_frndly(url)


def reboot_device(url):
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

    if state is "active":
        if app not in [int(channel_id_1), int(channel_id_2), int(channel_id_3)]:
            print("need to power on device at", device_url)
            send_request(device_url, pwr_on)

        # Check to see if Netflix is active, if so exit app before starting new show
        if app == 12:
            exit_netflix(device_url)
            time.sleep(1)
        # Check to see if Pluto is active, if so exit app before starting new show
        if app == 74519:
            exit_pluto(device_url)
            time.sleep(1)

        send_request(device_url, home)
        time.sleep(1)
        for i in range(6):
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, right)
        time.sleep(1)
        for i in range(12):
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, right)
        time.sleep(1)
        for i in range(7):
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, right)
        time.sleep(1)
        send_request(device_url, select)


# --- Main ---
while True:
    # Set commands for when a key is pressed
    # Keys only interact with the primary TV
    if neokey[0]:
        launch_channel(url_1, first_channel_id)

    if neokey[1]:
        launch_channel(url_1, second_channel_id)

    if neokey[2]:
        launch_channel(url_1, third_channel_id)

    if neokey[3]:
        power_off(url_1)

    if neokey_2[1]:
        volume_up(url_1)

    if neokey_2[2]:
        volume_down(url_1)

    # Interact with television, while watching Netflix, uses update_delay
    # which is set in the data.py file
    # If we don't do this, Netflix will prompt "Are you still watching"
    if last_check is None or time.monotonic() > last_check + update_delay:
        # Set loading display
        set_loading_display_msg()

        # Get current time
        now = get_time(True)

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
            secondary_active_app = get_active_app(url_2)
            print("secondary device active app is", secondary_active_app)

        # Set the default menu of what to watch
        set_default_display_msg()
        print("Ready to begin handling devices")

        last_check = time.monotonic()

    # If either TV is on and Netflix is playing
    # Interact with the TV to avoid the "are you still watching message"
    # Also handle turning on/off each device daily
    if interact_check is None or time.monotonic() > interact_check + interact_delay:
        now = get_time(False)

        if default_display is False:
            set_default_display_msg()

        # Hard reboot remote - just to flush out any bad things
        if (now[3] == remote_reboot_time[0] and now[4] >= remote_reboot_time[1]) and \
                (now[3] == remote_reboot_time[0] and now[4] <= remote_reboot_time[1] + 5):
            print("resetting device")
            microcontroller.reset()

        if primary_device_state is "active":
            if primary_active_app == first_channel_id:
                interact_with_tv(url_1)

        if secondary_device_state is "active":
            if secondary_active_app == first_channel_id:
                interact_with_tv(url_2)

        # Reboot the TV - new day, fresh start
        if primary_tv_start_time[1] == 0:
            primary_tv_reboot_minutes = 40
            primary_tv_reboot_hour = primary_tv_start_time[0] - 1
        else:
            primary_tv_reboot_hour = primary_tv_start_time[0]
            primary_tv_reboot_minutes = primary_tv_start_time[1] - 20
        if now[3] == primary_tv_reboot_hour and now[4] >= primary_tv_reboot_minutes:
            if primary_reboot is True:
                print("rebooting LR TV")
                reboot_device(url_1)
            primary_reboot = False

        # Turn on the primary TV each morning
        if now[3] == primary_tv_start_time[0] and now[4] >= primary_tv_start_time[1]:
            if primary_device_state is "active":
                if primary_tv_channel is channel_1:
                    if primary_active_app != first_channel_id:
                        launch_channel(url_1, first_channel_id)
                elif primary_tv_channel is channel_2:
                    if primary_active_app != second_channel_id:
                        if primary_active_app == 12:
                            wake_up_netflix(url_1)
                        launch_channel(url_1, second_channel_id)
                        confirm_pluto_show_loaded(url_1)
                elif primary_tv_channel is channel_3:
                    if secondary_active_app != third_channel_id:
                        launch_channel(url_1, third_channel_id)

        # Turn off the primary TV each night
        if now[3] == primary_tv_end_time[0] and now[4] >= primary_tv_end_time[1]:
            if primary_device_state is "active":
                power_off(url_1)

            primary_reboot = True

        # Reboot secondary TV each afternoon
        if now[3] == secondary_tv_start_time[0] and now[4] >= secondary_tv_start_time[1] - 10:
            if secondary_reboot is True:
                print("rebooting secondary TV")
                reboot_device(url_2)
            secondary_reboot = False

        # Turn on the secondary TV each evening
        if now[3] == secondary_tv_start_time[0] and now[4] >= secondary_tv_start_time[1]:
            if secondary_device_state is "active":
                if secondary_tv_channel is channel_1:
                    if secondary_active_app != first_channel_id:
                        second_tv = True
                        set_secondary_tv_start_msg()
                        launch_channel(url_2, first_channel_id)
                elif secondary_tv_channel is channel_2:
                    if secondary_active_app != second_channel_id:
                        second_tv = True
                        set_secondary_tv_start_msg()
                        if secondary_active_app == 12:
                            wake_up_netflix(url_2)
                        launch_channel(url_2, second_channel_id)
                        confirm_pluto_show_loaded(url_2)
                elif secondary_tv_channel is channel_3:
                    if secondary_active_app != third_channel_id:
                        second_tv = True
                        set_secondary_tv_start_msg()
                        launch_channel(url_2, third_channel_id)

        # Turn off the secondary TV each night
        if now[3] == secondary_tv_end_time[0] and now[4] >= secondary_tv_end_time[1]:
            if secondary_device_state is "active":
                power_off(url_2)

            secondary_reboot = True

        interact_check = time.monotonic()

    time.sleep(0.05)
