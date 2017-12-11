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

STATSFILE = '/proc/diskstats'
BLINKRATE = 0.065
DEVICENAME = 2
DEVICE = 'sda'
IOINPROGRESS = 11
ICONWIDTH = 32
ICONHEIGHT = 32

def resetled():
    icon.icon = iconoff
    icon.visible = True
    print 'OFF'

def setled():
    global timer
    if 'timer' in globals():
        if timer.is_alive:
            timer.cancel()
    timer = threading.Timer(BLINKRATE, resetled)
    timer.start()
    icon.icon = iconon
    icon.visible = True
    print 'ON'

def getstat(device):
    lststats=[]
    stats = open(STATSFILE).readlines()
    for stat in stats:
        lstat = stat.split()
        if lstat[DEVICENAME] == device:
            return lstat
    return None

def getioinprogress(device):
    stat = getstat(device)
    if stat:
        return int(stat[IOINPROGRESS])
    return 0

def image_on():
    image = Image.new('RGB', (ICONWIDTH, ICONHEIGHT), "#FF0000")
    dc = ImageDraw.Draw(image)
    dc.arc(xy = [(0,0), (ICONWIDTH-2,ICONHEIGHT-2)], start = 0, end = 360, fill = "#FF0000")
    return image

def image_off():
    image = Image.new('RGB', (ICONWIDTH, ICONHEIGHT), "#000000")
    dc = ImageDraw.Draw(image)
    dc.arc(xy = [(0,0), (ICONWIDTH-2,ICONHEIGHT-2)], start = 0, end = 360, fill = "#000000")
    return image

def startup(myicon):
    resetled()
    while True:
        weightedtime = getioinprogress(DEVICE)
        #print weightedtime
        if weightedtime > 0:
            setled()
        time.sleep(BLINKRATE / 4.0)

if __name__ == '__main__':
    icon = pystray.Icon('dsklite')
    iconon = image_on()
    iconoff = image_off()
    icon.icon = iconoff
    icon.visible = True
    icon.title = "Disk Activity"
    icon.run(startup)
    #icon.run()
