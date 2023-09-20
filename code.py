# SPDX-License-Identifier: MIT
# This is a very simple remote, designed for individuals with difficulty navigating
# all the different streaming applications
# It was designed to help a senior have less frustration while trying to watch television
import ssl
import time
import board
import displayio
import re
import socketpool
import wifi
import adafruit_requests
import adafruit_ntp
import adafruit_logging as logger
from adafruit_neokey.neokey1x4 import NeoKey1x4

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

# Get what we need from the data file
hosts = data["device_hosts"]
port = data["service_port"]
current_shows = data["shows"]
current_channels = data["channels"]
channel_ids = data["channel_numbers"]
pluto_shows = data["pluto_shows_array"]
roku_shows = data["roku_shows_array"]
paramount_shows = data["paramount_shows_array"]
netflix_search_int = data["netflix_search_array"]
primary_tv_start_time = data["primary_tv_start_time"]
primary_tv_end_time = data["primary_tv_end_time"]
primary_tv_channel = data["primary_tv_channel"]
secondary_tv_start_time = data["secondary_tv_start_time"]
secondary_tv_end_time = data["secondary_tv_end_time"]
secondary_tv_channel = data["secondary_tv_channel"]
secondary_device = data["secondary_device_active"]
update_delay = data["update_delay"]
interact_delay = data["interact_delay"]
key_input_delay = data["key_input_delay"]
live_check = data["live_check"]
tz_offset = data["tz_offset"]
log_level = data["log_level"]

# --- Setup  ---

# Network Variables
SSID = secrets["ssid"]
WIFI_PASS = secrets["password"]

# Device Interaction Variables
INPUT_WAIT_TIME = key_input_delay
CHECK_STRING = live_check
TZ_OFFSET = float(tz_offset)
if secondary_device != 0:  # There is a second TV in the house
    SECOND_TV = True
else:  # There is only one TV
    SECOND_TV = False
CHOICE = 0
RUNNING_APP = 0
RUNNING_SHOW = None
LAST_CHECK = None
INTERACT_CHECK = None
PRIMARY_ACTIVE_APP = None
SECONDARY_ACTIVE_APP = None
PRIMARY_CHANNEL_NAME = None
SECONDARY_CHANNEL_NAME = None
PRIMARY_SHOW_NAME = None
SECONDARY_SHOW_NAME = None

# Logging
LOGGER = logger.getLogger('console')
if log_level is "debug":
    LOGGER.setLevel(logger.DEBUG)
elif log_level is "info":
    LOGGER.setLevel(logger.INFO)
elif log_level is "warning":
    LOGGER.setLevel(logger.WARNING)
elif log_level is "error":
    LOGGER.setLevel(logger.ERROR)
elif log_level is "critical":
    LOGGER.setLevel(logger.CRITICAL)
else:
    print("setting log level to critical")
    LOGGER.setLevel(logger.CRITICAL)

LOGGER.info("log level is " + log_level)

# URLs
URL_1 = ("http://" + hosts[0] + ":" + port + "/")
URL_2 = ("http://" + hosts[1] + ":" + port + "/")

# Host IPs, for ping check
HOST_1_IP = hosts[0]
HOST_2_IP = hosts[1]

# Build array of channel ID ints
CHANNEL_ID_INTS = []
for i in range(len(channel_ids)):
    CHANNEL_ID_INTS.append(int(channel_ids[i]))

# --- Network Setup --- #

# Socketpool and requests for talking to devices
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# NTP
ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)

# --- Neokey Setup --- #

color = displayio.Palette(7)
color[0] = 0XFF0000  # red = Show 1
color[1] = 0x008000  # green = Show 3

i2c_bus = board.STEMMA_I2C()
neokey = NeoKey1x4(i2c_bus, addr=0x30)

# Set colors for the keyboard
neokey.pixels[0] = color[1]
neokey.pixels[3] = color[0]


# --- Roku API Calls --- #
home = "keypress/home"  # Home
right = "keypress/right"  # Right
left = "keypress/left"  # Left
up = "keypress/up"  # Up
down = "keypress/down"  # Down
back = "keypress/back"  # Back
select = "keypress/select"  # Select
vol_up = "keypress/volumeup"  # Volume Up
vol_down = "keypress/volumedown"  # Volume Down
pwr_on = "keypress/poweron"  # Power On
pwr_off = "keypress/poweroff"  # Power Off
launch = "launch/"  # Launch a Channel
active_app = "query/active-app"  # Query Active Application
query_media = "query/media-player"  # Query Device State


# --- Helper methods not related to Roku devices --- #

# Get current time from NTP and return it
def get_time():
    cur_time = None

    while cur_time is None:
        try:
            cur_time = ntp.datetime
        except RuntimeError as e:
            LOGGER.error("get_time: An error occurred, retrying ... " + str(e))
            continue

    return cur_time


# Convert a show name to an array for searching
def get_show_search_array(show_to_watch):
    show_to_split = show_to_watch.split()
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


# --- Helper methods to assist in channel/show launching --- #

# Set global variables needed to interact with the devices
def set_channel_and_show(url, show_to_watch):
    global PRIMARY_CHANNEL_NAME, SECONDARY_CHANNEL_NAME, PRIMARY_SHOW_NAME, SECONDARY_SHOW_NAME, \
        PRIMARY_ACTIVE_APP, SECONDARY_ACTIVE_APP

    show_configured = False

    while show_configured is False:
        for show in range(len(current_shows)):
            if show_to_watch is current_shows[show]:
                channel_to_watch = current_channels[show]
                app_to_watch = channel_ids[show]
                if url is URL_1:
                    PRIMARY_CHANNEL_NAME = channel_to_watch
                    PRIMARY_SHOW_NAME = show_to_watch
                    PRIMARY_ACTIVE_APP = int(app_to_watch)
                else:
                    SECONDARY_CHANNEL_NAME = channel_to_watch
                    SECONDARY_SHOW_NAME = show_to_watch
                    SECONDARY_ACTIVE_APP = int(app_to_watch)
                show_configured = True


# Use in-channel search to locate show to watch
# Using search as a more reliable way to find what to watch
def search_program(url, show_to_watch):
    if url:
        device_url = url
    else:
        device_url = URL_1

    search_show = get_show_search_array(show_to_watch)
    time.sleep(1)

    for letter in search_show:
        command = ("keypress/Lit_" + letter)
        send_request(device_url, command)
        time.sleep(0.5)


# Query the devices to determine if they are online
def get_device_state(url):
    device_state = "inactive"

    if url:
        device_url = url
    else:
        device_url = URL_1

    LOGGER.debug("get_device_state: querying " + str(device_url) + " for status")
    if send_request(device_url, query_media) is not None:
        device_state = "active"

    return device_state


# Get the active app ID
def get_active_app(url):
    active_channel = 0

    if url:
        device_url = url
    else:
        device_url = URL_1

    if device_url is URL_1:
        app_state = primary_device_state
        app_id_to_check = PRIMARY_ACTIVE_APP
    else:
        app_state = secondary_device_state
        app_id_to_check = SECONDARY_ACTIVE_APP

    if app_state is "active" and app_id_to_check is None:
        LOGGER.debug("get_active_app: Attempting to get active channel for device " + str(device_url))
        channel_text = send_request(device_url, active_app)
        if channel_text is not None:
            regex = re.compile("[\r\n]")
            parsed_response = regex.split(channel_text)
            regex = re.compile("[\"]")
            tmp_channel = (regex.split(parsed_response[2]))
            active_channel = tmp_channel[1]
        else:
            LOGGER.critical("get_active_app: failed to get response from device for active channel")
    else:
        print("already have active app for URL")
        active_channel = app_id_to_check

    LOGGER.debug("active app is now set to " + str(active_channel))

    return active_channel


# Determine which item we want in a channel's watch list
# This only works as long as the show stays in the watch list after viewing it
#    and the app doesn't shift the position of the items in the watch list based
#    on what was watched most recently
def get_addtl_show_info(show_to_watch, channel):
    position = 0
    search_array = []
    if channel is "Pluto":
        search_array = pluto_shows
    if channel is "Roku":
        search_array = roku_shows
    if channel is "Paramount":
        search_array = paramount_shows
    if channel is "Netflix":
        search_array = netflix_search_int

    for show in range(len(search_array)):
        if show_to_watch in search_array[show]:
            show = search_array[show]
            position = show[1]
    return position


# Send command to appropriate Roku device
def send_request(url, command):
    result = None

    try:
        if "active-app" in command:
            LOGGER.debug("querying for active app")
            response = requests.get(url + command)
            result = response.text
            response.close()
        elif "media-player" in command:
            LOGGER.debug("querying media player")
            response = requests.get(url + command)
            result = response.text
            response.close()
        else:
            response = requests.post(url + command)
            result = "true"
            response.close()
    except Exception as e:
        LOGGER.error("send_request: Caught generic exception " + str(e) + " for command " + str(command))

    return result


# Exit current running app and power down the Roku TV or put the Roku device into sleep mode
def power_off(url):
    LOGGER.info("request to power off")
    if url:
        device_url = url
    else:
        device_url = URL_1

    if device_url is URL_1:
        app = PRIMARY_ACTIVE_APP
    else:
        app = SECONDARY_ACTIVE_APP

    # Check to see if we need to properly exit or if we can just return to home screen
    if app == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif app == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    else:
        send_request(device_url, home)
        time.sleep(1)

    send_request(device_url, pwr_off)


# Return to home screen, needed when we don't know the current state
def return_home(url):
    LOGGER.debug("eject Buckaroo!")
    if url:
        device_url = url
    else:
        device_url = URL_1

    if device_url is URL_1:
        app = PRIMARY_ACTIVE_APP
    else:
        app = SECONDARY_ACTIVE_APP

    # Check to see if we need to properly exit or if we can just return to home screen
    if app == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif app == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    else:
        send_request(device_url, home)
        time.sleep(1)

# --- Helper methods to launch, exit, and search within open channels --- #

# --- Netflix --- #


def launch_netflix(url, show_to_watch, app):
    if url:
        device_url = url
    else:
        device_url = URL_1

    if device_url is URL_1:
        channel = PRIMARY_CHANNEL_NAME
        show = PRIMARY_SHOW_NAME
    else:
        channel = SECONDARY_CHANNEL_NAME
        show = SECONDARY_SHOW_NAME

    # Check to see if we need to properly exit or if we can just return to home screen
    if RUNNING_APP == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    elif RUNNING_APP != int(app):
        send_request(device_url, home)
        time.sleep(1)

    channel_call = (launch + str(app))

    if RUNNING_APP == app:
        LOGGER.debug(str(app) + " is already running")
        current_show = RUNNING_SHOW
        show_letters_array = get_show_search_array(current_show)
        LOGGER.debug("need to remove " + str(len(show_letters_array)) + " before new search")
        for nav in range(2):
            send_request(device_url, back)
            time.sleep(1)
        send_request(device_url, left)
        time.sleep(1)
        for letter in range(len(show_letters_array)):
            send_request(device_url, select)
            time.sleep(0.5)
        send_request(device_url, left)
        time.sleep(1)
    else:
        LOGGER.debug(str(app) + " is not running, will launch channel")
        send_request(device_url, channel_call)  # launch Netflix
        time.sleep(15)
        # This is only for a multi-profile account
        # Comment out if only one profile
        send_request(device_url, select)  # select the active profile
        time.sleep(2)
        send_request(device_url, left)  # open the left nav menu
        time.sleep(1)
        send_request(device_url, up)  # navigate to Search
        time.sleep(1)
        send_request(device_url, select)
        time.sleep(1)

    search_program(url, show_to_watch)
    time.sleep(1)
    search_int = get_addtl_show_info(show_to_watch, channel)
    for nav in range(search_int):
        send_request(device_url, right)
        time.sleep(1)
    send_request(device_url, select)
    time.sleep(1)
    send_request(device_url, select)  # Start the show, don't wait for autostart

    LOGGER.info("launched " + str(show_to_watch) + " on " + str(channel) + " on device " + str(device_url))


# Exit Netflix properly to ensure we return to a known location
def exit_netflix(url):
    if url:
        device_url = url
    else:
        device_url = URL_1

    return_range = 4

    LOGGER.info("exiting Netflix")
    for x in range(return_range):  # Get back to left nav
        send_request(device_url, back)
        time.sleep(1)
    send_request(device_url, down)  # Return to home screen
    time.sleep(1)
    send_request(device_url, select)  # Return to home screen
    time.sleep(0.5)
    send_request(device_url, left)  # Return to left nav
    time.sleep(1)
    # Only needed if using a multi-profile account
    for nav in range(4):  # Move up to the profile
        send_request(device_url, up)
        time.sleep(1)
    send_request(device_url, select)  # Select it to land on profiles page
    time.sleep(1)
    send_request(device_url, home)


# Netflix likes to save your data by asking "are you still watching"
# Since we don't worry about that on these devices, interacting
# with the TV periodically will prevent them from popping up
def interact_with_netflix(url):
    if url:
        device_url = url
    else:
        device_url = URL_1

    netflix_show_status = send_request(device_url, query_media)
    if "pause" in netflix_show_status or "stop" in netflix_show_status:
        print("")
    else:
        LOGGER.debug("interact_with_tv: Interacting with TV to avoid Netflix prompt")
        send_request(device_url, up)
        time.sleep(1)

# --- Pluto --- #


def launch_pluto(url, show_to_watch, app):
    if url:
        device_url = url
    else:
        device_url = URL_1

    # Check to see if Netflix is active, if so exit app before starting new show
    if RUNNING_APP == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif RUNNING_APP != int(app):
        send_request(device_url, home)

    if device_url is URL_1:
        channel = PRIMARY_CHANNEL_NAME
        show = PRIMARY_SHOW_NAME
    else:
        channel = SECONDARY_CHANNEL_NAME
        show = SECONDARY_SHOW_NAME

    watch_list_pos = get_addtl_show_info(show_to_watch, channel)

    # Don't relaunch the app if already watching, just move back to root of On Demand Menu
    # Otherwise launch the app and navigate to On Demand Menu
    if RUNNING_APP == int(app):
        LOGGER.debug(str(app) + " already running")
        for nav in range(3):
            send_request(device_url, back)
            time.sleep(1)
    else:
        LOGGER.debug(str(app) + " not running, launch app")
        channel_call = (launch + str(app))
        wait_for_start = True
        send_request(device_url, channel_call)  # launch Pluto TV

        while wait_for_start is True:
            # Check to see if currently streaming live tv
            if CHECK_STRING in send_request(url, query_media):
                wait_for_start = False
                LOGGER.debug("station loaded, ready to proceed")
            else:
                LOGGER.debug("waiting for channel to launch")
                time.sleep(4)
        LOGGER.debug("start launch procedure")
        for nav in range(2):  # Open left nav, hit left twice in case the Guide button has timed out
            send_request(device_url, left)
            time.sleep(1)
        for nav in range(2):
            send_request(device_url, down)  # Navigate to On Demand
            time.sleep(1)
        send_request(device_url, select)  # Select On Demand
        time.sleep(1)

    for nav in range(2):
        send_request(device_url, down)  # Navigate to Watch List
        time.sleep(2)
    for nav in range(watch_list_pos):
        send_request(device_url, right)  # Move to the chosen show in the watch list
        time.sleep(1)
    send_request(device_url, select)
    time.sleep(1)
    send_request(device_url, select)
    time.sleep(5)
    confirm_pluto_show_loaded(device_url, show_to_watch)

    LOGGER.info("launched " + str(show_to_watch) + " on " + str(channel) + " on device " + str(device_url))


# Check that chosen show actually loaded the program we want
def confirm_pluto_show_loaded(url, show_to_watch):
    show_launched = False

    if url:
        device_url = url
    else:
        device_url = URL_1

    LOGGER.debug("confirming chosen PlutoTV show has launched")
    while show_launched is False:

        # Check to see if currently streaming live tv
        if CHECK_STRING in send_request(url, query_media):
            LOGGER.warning("Didn't launch chosen show, trying again")
            launch_channel(device_url, 74519, show_to_watch)  # attempt to relaunch show
        else:
            LOGGER.info("Chosen show successfully launched")
            show_launched = True

        time.sleep(2)


# Exit Pluto properly so that we're at a known good starting spot upon return
def exit_pluto(url):
    if url:
        device_url = url
    else:
        device_url = URL_1

    # Check to see if currently streaming live tv
    if CHECK_STRING in send_request(url, query_media):
        return_range = 4
    else:
        return_range = 5

    LOGGER.info("exiting Pluto")
    for x in range(return_range):  # Exit App
        send_request(device_url, back)
        time.sleep(2)
    send_request(device_url, down)  # Navigate to Exit App in selection
    time.sleep(1)
    send_request(device_url, select)  # Exit app, return to home screen

# --- YouTube TV --- #


def launch_youtubetv(url, show_to_watch, app):
    if url:
        device_url = url
    else:
        device_url = URL_1

    # Check to see if we need to properly exit or if we can just return to home screen
    if RUNNING_APP == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif RUNNING_APP == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    elif RUNNING_APP != int(app):
        send_request(device_url, home)
        time.sleep(1)

    if device_url is URL_1:
        channel = PRIMARY_CHANNEL_NAME
        show = PRIMARY_SHOW_NAME
    else:
        channel = SECONDARY_CHANNEL_NAME
        show = SECONDARY_SHOW_NAME

    channel_call = (launch + str(app))

    if RUNNING_APP is app and RUNNING_SHOW is not "Steelers":
        youtube_return_to_search(device_url)
    else:
        if RUNNING_SHOW is "Steelers":
            return_home(device_url)
        time.sleep(2)
        send_request(device_url, channel_call)  # launch YouTube TV
        time.sleep(15)
        for nav in range(3):
            send_request(device_url, right)  # Navigate to search
            time.sleep(3)
        send_request(device_url, down)  # Enter search
        time.sleep(1)

    search_program(device_url, show_to_watch)  # Search for channel
    time.sleep(1)
    for nav in range(2):
        send_request(device_url, right)  # Navigate to searched channel
        time.sleep(2)
    send_request(device_url, select)
    time.sleep(1)
    if show_to_watch is "Steelers":
        for nav in range(2):
            send_request(device_url, select)
            time.sleep(1)
    else:
        send_request(device_url, down)
        time.sleep(1)
        for a in range(2):
            send_request(device_url, select)
            time.sleep(1)
        time.sleep(1)

    LOGGER.info("launched " + str(show_to_watch) + " on " + str(channel) + " on device " +  str(device_url))


# Return to search menu and clear prior search for YouTube
def youtube_return_to_search(url):
    nav_range = 4

    for nav in range(nav_range):
        send_request(url, back)
        time.sleep(0.5)
    send_request(url, right)
    time.sleep(1)
    for nav in range(6):
        send_request(url, down)
        time.sleep(0.5)
    send_request(url, select)
    time.sleep(1)
    for nav in range(6):
        send_request(url, up)
        time.sleep(0.5)
    send_request(url, left)
    time.sleep(1)

# --- Roku --- #


def launch_roku(url, show_to_watch, app):
    if url:
        device_url = url
    else:
        device_url = URL_1

    # Check to see if we need to properly exit or if we can just return to home screen
    if RUNNING_APP == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif RUNNING_APP == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    elif RUNNING_APP != int(app):
        send_request(device_url, home)
        time.sleep(1)

    if device_url is URL_1:
        channel = PRIMARY_CHANNEL_NAME
    else:
        channel = SECONDARY_CHANNEL_NAME

    channel_call = (launch + str(app))

    show_pos = get_addtl_show_info(show_to_watch, channel)

    # Don't relaunch the app, just navigate back to the Save List
    # Otherwise, launch the app and navigate to the Save List
    if RUNNING_APP == int(app):
        LOGGER.debug(str(app) + " already running")
        for nav in range(3):
            send_request(device_url, back)
            time.sleep(1)
        for nav in range(2):
            send_request(device_url, left)
            time.sleep(1)
        send_request(device_url, select)
        time.sleep(0.5)
    else:
        LOGGER.debug(str(app) + " not running, need to launch Roku")
        send_request(device_url, channel_call)
        time.sleep(5)
        send_request(device_url, left)
        for nav in range(8):
            send_request(device_url, down)
            time.sleep(1)
        send_request(device_url, select)
        for nav in range(6):
            send_request(device_url, down)
            time.sleep(0.5)

    search_program(device_url, show_to_watch)
    for nav in range(3):
        send_request(device_url, right)
        time.sleep(1)

    if show_pos == 1:  # Certain search results have search breadcrumbs
        send_request(device_url, down)
        time.sleep(1)

    for nav in range(2):
        send_request(device_url, select)
        time.sleep(1)

    LOGGER.info("launched " + str(show_to_watch) + " on " + str(channel) + " on device " + str(device_url))


# --- Paramount+ --- #

def launch_paramount(url, show_to_watch, app):
    if url:
        device_url = url
    else:
        device_url = URL_1

    # Check to see if we need to properly exit or if we can just return to home screen
    if RUNNING_APP == 12:
        exit_netflix(device_url)
        time.sleep(1)
    elif RUNNING_APP == 74519:
        exit_pluto(device_url)
        time.sleep(1)
    elif RUNNING_APP != int(app):
        send_request(device_url, home)
        time.sleep(1)

    if device_url is URL_1:
        channel = PRIMARY_CHANNEL_NAME
    else:
        channel = SECONDARY_CHANNEL_NAME

    channel_call = (launch + str(app))

    if RUNNING_APP == app:
        LOGGER.debug(str(app) + " already running")
        running_show_pos = get_addtl_show_info(RUNNING_SHOW, channel)
        LOGGER.debug("current show position in array is " + str(running_show_pos))
        for nav in range(2):
            send_request(device_url, back)
            time.sleep(1)
        if running_show_pos != 0:
            for nav in range(running_show_pos):
                send_request(device_url, left)
                time.sleep(0.5)
    else:
        LOGGER.debug(str(app) + " not running, launching channel")
        send_request(device_url, channel_call)  # launch Paramount+
        time.sleep(10)
        send_request(device_url, right)  # Navigate to second profile
        time.sleep(2)
        send_request(device_url, select)  # Select second profile
        time.sleep(5)
        send_request(device_url, left)  # Access lef nav
        time.sleep(1)
        for a in range(7):
            send_request(device_url, down)  # Move Down to My List
            time.sleep(1)
        send_request(device_url, select)  # Select My List
        time.sleep(2)

    show_pos = get_addtl_show_info(show_to_watch, channel)
    LOGGER.debug("show pos is " + str(show_pos))
    for nav in range(show_pos):
        send_request(device_url, right)
        time.sleep(0.5)
    send_request(device_url, select)  # Select the first show in the list
    time.sleep(2)
    send_request(device_url, select)  # Start playing the show

    LOGGER.info("launched  " + str(show_to_watch) + " on " + str(channel) + " on device " + str(device_url))


# --- The mac daddy of launch methods : the case statement for which channel to launch

def launch_channel(url, app, show_to_watch):
    if app == 195316:
        print("launching channel on YouTube TV")
        launch_youtubetv(url, show_to_watch, 195316)
    if app == 12:
        print("launching show on Netflix")
        launch_netflix(url, show_to_watch, 12)
    if app == 74519:
        print("launching show on pluto")
        launch_pluto(url, show_to_watch, 74519)
    if app == 31440:
        print("launching show on paramount")
        launch_paramount(url, show_to_watch, app)
    if app == 151908:
        print("launching show on Roku")
        launch_roku(url, show_to_watch, 151908)

# --- Channel/show selection via the buttons

# One button operation allows TV watcher to cycle through shows/channels
# provided in the data file. This can be as many as you want
# Use audio queues to confirm we want to watch the current selection


def select_what_to_watch(url):
    global CHOICE, RUNNING_APP, RUNNING_SHOW

    last_input_check = 0
    launch_selection = False

    if url is URL_1:
        RUNNING_APP = PRIMARY_ACTIVE_APP
        RUNNING_SHOW = PRIMARY_SHOW_NAME
    else:
        RUNNING_APP = SECONDARY_ACTIVE_APP
        RUNNING_SHOW = SECONDARY_SHOW_NAME

    if RUNNING_APP is None:
        print("Primary active app is undefined", AttributeError)
        raise

    if CHOICE >= len(current_channels) - 1:
        CHOICE = 0

    if PRIMARY_SHOW_NAME is current_shows[CHOICE]:
        print("incrementing")
        CHOICE += 1

    announce_choice(url, current_channels[CHOICE], current_shows[CHOICE])

    while launch_selection is False:
        now = time.monotonic()

        if last_input_check == 0:
            last_input_check = now

        if now >= last_input_check + INPUT_WAIT_TIME:
            # Don't know current state and we're starting a new show, so escape to home screen for safety
            # Likely the remote restarted while a show was playing
            if RUNNING_SHOW is None and RUNNING_SHOW is not current_shows[CHOICE]:
                return_home(url)

            if RUNNING_SHOW is current_shows[CHOICE]:
                if PRIMARY_SHOW_NAME is None:
                    set_channel_and_show(url, current_shows[CHOICE])  # update global variables
                print("same show selected as what's playing, do nothing")
            else:
                set_channel_and_show(url, current_shows[CHOICE])  # update global variables
                time.sleep(1)
                launch_channel(url, PRIMARY_ACTIVE_APP, PRIMARY_SHOW_NAME)

            launch_selection = True
        else:
            if neokey[0]:
                change_choice(url)  # Move to next show/channel and announce it
                # Reset the wait period
                last_input_check = time.monotonic()
        time.sleep(0.25)


# If the primary input key is pressed during wait period increment where we are
# in the array of shows and channels
def change_choice(url):
    global CHOICE

    if CHOICE >= len(current_channels) - 1:
        CHOICE = 0
    else:
        CHOICE += 1

    announce_choice(url, current_channels[CHOICE], current_shows[CHOICE])


# Announce the currently selected show and channel
def announce_choice(url, channel_to_announce, show_to_announce):

    print("Will start", show_to_announce, "on", channel_to_announce, "press the green button if you want"
                                                                     "to watch something else")


# --- Main ---

# Connect to the local network
print("attempting to connect to network")
wifi.radio.connect(SSID, WIFI_PASS)
print("Connected to %s" % SSID)

# Get the device states for all active devices
primary_device_state = get_device_state(URL_1)
time.sleep(2)
if SECOND_TV is True:
    secondary_device_state = get_device_state(URL_2)
    time.sleep(2)
print("done getting device states")

# Get the active apps, if an active app hasn't been sent None will be returned
PRIMARY_ACTIVE_APP = get_active_app(URL_1)
print("primary active app is", PRIMARY_ACTIVE_APP)
if SECOND_TV is True:
    SECONDARY_ACTIVE_APP = get_active_app(URL_2)
print("done getting active apps")

while True:

    # Set commands for when a key is pressed
    # Keys only interact with the primary TV
    if neokey[0]:
        time.sleep(0.25)
        select_what_to_watch(URL_1)

    if neokey[3]:
        power_off(URL_1)

    # If either TV is on and Netflix is playing
    # Interact with the TV to avoid the "are you still watching message"
    if INTERACT_CHECK is None or time.monotonic() > INTERACT_CHECK + interact_delay:

        if primary_device_state is "active":
            if PRIMARY_ACTIVE_APP == 12:
                interact_with_netflix(URL_1)

        if SECOND_TV is True:
            if secondary_device_state is "active":
                if SECONDARY_ACTIVE_APP == 12:
                    interact_with_netflix(URL_2)

        INTERACT_CHECK = time.monotonic()

    time.sleep(0.05)
