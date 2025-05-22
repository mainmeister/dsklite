"""
What:		/proc/diskstats
Date:		February 2008
Contact:	Jerome Marchand <jmarchan@redhat.com>
Description:
		The /proc/diskstats file displays the I/O statistics
		of block devices. Each line contains the following 14
		fields:
		 1 - major number
		 2 - minor mumber
		 3 - device name
		 4 - reads completed successfully
		 5 - reads merged
		 6 - sectors read
		 7 - time spent reading (ms)
		 8 - writes completed
		 9 - writes merged
		10 - sectors written
		11 - time spent writing (ms)
		12 - I/Os currently in progress
		13 - time spent doing I/Os (ms)
		14 - weighted time spent doing I/Os (ms)
		For more details refer to Documentation/iostats.txt

example:
   7       0 loop0 0 0 0 0 0 0 0 0 0 0 0
   7       1 loop1 0 0 0 0 0 0 0 0 0 0 0
   7       2 loop2 0 0 0 0 0 0 0 0 0 0 0
   7       3 loop3 0 0 0 0 0 0 0 0 0 0 0
   7       4 loop4 0 0 0 0 0 0 0 0 0 0 0
   7       5 loop5 0 0 0 0 0 0 0 0 0 0 0
   7       6 loop6 0 0 0 0 0 0 0 0 0 0 0
   7       7 loop7 0 0 0 0 0 0 0 0 0 0 0
   8       0 sda 687090 112702 58638000 6132652 1812074 3208268 192392230 45087140 0 15660532 51216212
   8       1 sda1 686973 112702 58629324 6130924 1402204 3208187 192391574 41370476 0 12433160 47497668
   8       2 sda2 2 0 4 72 0 0 0 0 0 72 72
   8       5 sda5 44 0 4408 532 1 81 656 24 0 552 556
  11       0 sr0 27 0 120 36 0 0 0 0 0 36 36
   8      16 sdb 0 0 0 0 0 0 0 0 0 0 0


*** Using system tray see https://github.com/moses-palmer/pystray
Creating a system tray icon

In order to create a system tray icon, the class pystray.Icon is used:

import pystray

icon = pystray.Icon('test name')
In order for the icon to be displayed, you must provide an icon. This icon must be specified as a PIL.Image.Image:

from PIL import Image, ImageDraw

def create_image():
    # Generate an image and draw a pattern
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image

icon.icon = create_image()
To finally show you icon, run the following code:

icon.run()
The call to pystray.Icon.run() is blocking, and it must be performed from the main thread of the application. The reason for this is that the system tray icon implementation for OSX will fail unless called from the main thread, and it also requires the application runloop to be running. pystray.Icon.run() will start the runloop.

The run() method accepts an optional argument: setup, a callable.

The setup funciton will be run in a separate thread once the system tray icon is ready. The icon does not wait for it to complete, so you may put any code that would follow the call to pystray.Icon.run() in it.

The call to pystray.Icon.run() will not complete until stop() is called.

Getting input from the system tray icon

In order to receive notifications about user interaction with the icon, a popup menu can be added with the menu constructor argument.

This must be an instance of pystray.Menu. Please see the reference for more information about the format.

It will be displayed when the right-hand button has been pressed on the icon on Windows, and when the icon has been clicked on other platforms. Menus are not supported on X.

Menus also support a default item. On Windows, and X, this item will be activated when the user clicks on the icon using the primary button. On other platforms it will be activated if the menu contains no visible entries; it does not have to be visible.

All properties of menu items, except for the callback, can be dynamically calculated by supplying callables instead of values to the menu item constructor. The properties are recalculated every time the icon is clicked or any menu item is activated.

If the dynamic properties change because of an external event, you must ensure that Icon.update_menu is called. This is required since not all supported platforms allow for the menu to be generated when displayed.

Creating the menu

A menu consists of a list of menu items, optionally separated by menu separators.

Separators are intended to group menu items into logical groups. They will not be displayed as the first and last visible item, and adjacent separators will be hidden.

A menu item has several attributes:

text and action
The menu item text and its associated action.

These are the only required attribute.

checked
Whether the menu item is checked.

This can be one of three values:

False
The item is decorated with an unchecked check box.
True
The item is decorated with a checked check box.
None
There is no hint that the item is checkable.
If you want this to actually be togglable, you must pass a callable that returns the current state:

state = False

def on_clicked(icon, item):
    global state
    state = not item.checked

# Update the state in `on_clicked` and return the new state in
# a `checked` callable
Icon('test', create_image(), menu=Menu(
    MenuItem(
        'Checkable',
        on_clicked,
        checked=lambda item: state))).run()
radio
Whether this is a radio button.

This is used only if checked is True or False, and only has a visual meaning. The menu has no concept of radio button groups:

state = 0

def set_state(v):
    def inner(icon, item):
        global state
        state = v
    return inner

def get_state(v):
    def inner(item):
        return state == v
    return inner

# Let the menu items be a callable returning a sequence of menu
# items to allow the menu to grow
Icon('test', create_image(), menu=Menu(lambda: (
    MenuItem(
        'State %d' % i,
        set_state(i),
        checked=get_state(i),
        radio=True)
    for i in range(max(5, state + 2))))).run()
default
Whether this is the default item.

It is drawn in a distinguished style and will be activated as the default item on platforms that support default actions. On X, this is the only action available.

visible
Whether the menu item is visible.
enabled
Whether the menu item is enabled. Disabled menu items are displayed, but are greyed out and cannot be activated.
submenu
The submenu, if any, that is attached to this menu item.

If this is set, the action will not be called.

Once created, menus and menu items cannot be modified. All attributes except for the menu item callbacks can however be set to callables returning the current value. This also applies to the sequence of menu items belonging to a menu: this can be a callable returning the current sequence.
"""

import threading
import time
import pystray
from PIL import Image, ImageDraw, ImageColor
import sys

STATSFILE = '/proc/diskstats'
BLINKRATE = 0.065
DEVICENAME = 2
DEVICE = 'sda'
IOINPROGRESS = 11
ICONWIDTH = 32
ICONHEIGHT = 32

timer = None # Initialize timer globally
icon = None # Initialize icon globally, will be set in main
iconon_img = None # Global for the 'on' image
iconoff_img = None # Global for the 'off' image

def resetled_icon_state():
    global icon, iconoff_img
    if icon and iconoff_img:
        try:
            icon.icon = iconoff_img
            icon.visible = True
            # print 'OFF' # Optional: for debugging
        except Exception as e:
            # Log error if updating the pystray icon fails during runtime.
            # Recovery: Continue execution. The icon might be stale, but the monitoring loop proceeds.
            # This prevents a runtime glitch in UI update from crashing the whole application.
            sys.stderr.write(f"Error updating icon to OFF state: {e}\n")
    elif not icon:
        # This case should ideally not be reached if icon is initialized properly in startup_routine.
        sys.stderr.write("Error: resetled_icon_state called before icon was initialized.\n")
    elif not iconoff_img:
        # This case indicates an issue with image creation at startup.
        sys.stderr.write("Error: resetled_icon_state called before iconoff_img was created.\n")


def setled_icon_state():
    global timer, icon, iconon_img
    # Cancel any existing timer to ensure the icon-off action is correctly timed
    # from this 'setled_icon_state' call.
    if timer is not None and timer.is_alive():
        timer.cancel()
    
    try:
        # Start a timer to call resetled_icon_state, which will set the icon to 'off' after BLINKRATE.
        timer = threading.Timer(BLINKRATE, resetled_icon_state)
        timer.start()
    except Exception as e:
        # Log error if the timer cannot be started.
        # This compromises the blinking behavior (icon might stay 'on').
        # Recovery: Continue execution. Disk activity monitoring is still valuable.
        sys.stderr.write(f"Error starting timer in setled_icon_state: {e}\n")

    if icon and iconon_img:
        try:
            # Set the icon to 'on' state.
            icon.icon = iconon_img
            icon.visible = True
            # print 'ON' # Optional: for debugging
        except Exception as e:
            # Log error if updating the pystray icon fails during runtime.
            # Recovery: Continue execution. The icon might not update to 'on', but the monitoring loop proceeds.
            sys.stderr.write(f"Error updating icon to ON state: {e}\n")
    elif not icon:
        # This case should ideally not be reached.
        sys.stderr.write("Error: setled_icon_state called before icon was initialized.\n")
    elif not iconon_img:
        # This case indicates an issue with image creation at startup.
        sys.stderr.write("Error: setled_icon_state called before iconon_img was created.\n")


def getstat(device):
    try:
        with open(STATSFILE, 'r') as f:
            stats = f.readlines()
        for stat_line in stats:
            lstat = stat_line.split()
            # Check if the line is long enough and matches the target device.
            if len(lstat) > DEVICENAME and lstat[DEVICENAME] == device:
                return lstat
    except (IOError, OSError) as e:
        # Log error if STATSFILE cannot be read. This is a non-critical error for a single read attempt.
        # Recovery: Return None. getioinprogress will then return 0, indicating no activity.
        # The main loop will continue and retry reading on the next iteration.
        sys.stderr.write(f"Error reading STATSFILE '{STATSFILE}': {e}\n")
    except Exception as e: # Catch any other unexpected errors
        # Log unexpected errors during file processing.
        # Recovery: Return None, similar to IOError/OSError.
        sys.stderr.write(f"Unexpected error reading STATSFILE '{STATSFILE}': {e}\n")
    return None # Return None on error or if device not found

def getioinprogress(device):
    stat_data = getstat(device)
    if stat_data:
        if len(stat_data) > IOINPROGRESS:
            try:
                return int(stat_data[IOINPROGRESS])
            except ValueError as e:
                # Log error if the I/O progress value is not a valid integer.
                # Recovery: Return 0. Treating malformed data as no current I/O activity
                # is a safe default, preventing crashes and implying no icon change.
                sys.stderr.write(f"Error converting IOINPROGRESS to int for device '{device}': {e}\nData: {stat_data}\n")
        else:
            # Log if the expected field is missing.
            # Recovery: Return 0, as data is incomplete.
            sys.stderr.write(f"IOINPROGRESS index out of bounds for device '{device}'. Data: {stat_data}\n")
    # If stat_data is None (due to read error in getstat) or not structured as expected.
    # Recovery: Return 0. This is a safe default, indicating no I/O activity detected or data unavailable,
    # thus no need to change the icon state to 'on'.
    return 0

def create_image(color_hex):
    try:
        # Create a simple solid color image for the system tray icon.
        image = Image.new('RGB', (ICONWIDTH, ICONHEIGHT), color_hex)
        # Drawing an arc was an option, but a solid block is simpler and less prone to PIL issues.
        # dc = ImageDraw.Draw(image)
        # dc.arc(xy = [(0,0), (ICONWIDTH-2,ICONHEIGHT-2)], start = 0, end = 360, fill = color_hex)
        return image
    except Exception as e:
        # Log error if PIL/Pillow fails to create an image.
        # This is critical for the application's UI.
        # Recovery: Return None. The caller must handle this, usually by exiting at startup
        # or logging and attempting to continue if it's a non-critical runtime image update.
        sys.stderr.write(f"Error creating image with color {color_hex}: {e}\n")
        return None

def startup_routine(passed_icon): # pystray run() passes the icon as an argument
    # This function runs in a separate thread after the pystray icon is set up.
    global icon # Ensure we are using the global icon variable
    icon = passed_icon # Assign the passed icon to our global var for other functions to use
    
    resetled_icon_state() # Set initial state
    while True:
        weightedtime = getioinprogress(DEVICE)
        if weightedtime > 0:
            setled_icon_state()
        # If weightedtime is 0, the timer from the last setled_icon_state() will call resetled_icon_state()
        time.sleep(BLINKRATE / 4.0)

if __name__ == '__main__':
    # Create images first
    # Create images for 'on' and 'off' states at startup.
    iconon_img = create_image("#FF0000") # Red for ON
    iconoff_img = create_image("#000000") # Black for OFF (or a dim color)

    # PIL/Pillow image creation is essential for the system tray icon.
    # If images cannot be created, the application cannot display its state.
    # Recovery: Log a critical error and exit, as the application is not viable without icons.
    if iconon_img is None or iconoff_img is None:
        sys.stderr.write("Critical error: Failed to create initial icon images. Exiting.\n")
        sys.exit(1)

    try:
        # Initialize the pystray.Icon object. This is a core part of the application's UI.
        # Use a temporary variable for the icon passed to run, then assign to global in startup_routine.
        temp_icon = pystray.Icon(
            'dsklite',
            iconoff_img, # Initial icon state is 'off'.
            "Disk Activity"
        )
    except Exception as e:
        # Failure to create the pystray.Icon object is a critical startup error.
        # The application cannot function without the system tray icon.
        # Recovery: Log a critical error and exit.
        sys.stderr.write(f"Critical error: Failed to create pystray.Icon: {e}\n")
        sys.exit(1)
    
    try:
        # icon.run() is blocking and starts the system tray icon's event loop.
        # The 'setup' argument runs 'startup_routine' in a new thread.
        # This is the main entry point for the application's active monitoring.
        temp_icon.run(setup=startup_routine)
    except Exception as e:
        # If icon.run() itself fails (e.g., issues with the underlying OS tray mechanism),
        # the application cannot operate.
        # Recovery: Log a critical error and exit. Attempt to stop the icon if it was partially started.
        sys.stderr.write(f"Critical error: Failed during icon.run(): {e}\n")
        try:
            temp_icon.stop()
        except:
            # If stopping also fails, there's little more to do.
            pass # Ignore errors during stop attempt after a run failure
        sys.exit(1)
