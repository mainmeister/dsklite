#!/usr/bin/python2

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

Keyboard:
LED handling under Linux
========================

In its simplest form, the LED class just allows control of LEDs from
userspace. LEDs appear in /sys/class/leds/. The maximum brightness of the
LED is defined in max_brightness file. The brightness file will set the brightness
of the LED (taking a value 0-max_brightness). Most LEDs don't have hardware
brightness support so will just be turned on for non-zero brightness settings.

The class also introduces the optional concept of an LED trigger. A trigger
is a kernel based source of led events. Triggers can either be simple or
complex. A simple trigger isn't configurable and is designed to slot into
existing subsystems with minimal additional code. Examples are the disk-activity,
nand-disk and sharpsl-charge triggers. With led triggers disabled, the code
optimises away.

Complex triggers whilst available to all LEDs have LED specific
parameters and work on a per LED basis. The timer trigger is an example.
The timer trigger will periodically change the LED brightness between
LED_OFF and the current brightness setting. The "on" and "off" time can
be specified via /sys/class/leds/<device>/delay_{on,off} in milliseconds.
You can change the brightness value of a LED independently of the timer
trigger. However, if you set the brightness value to LED_OFF it will
also disable the timer trigger.

You can change triggers in a similar manner to the way an IO scheduler
is chosen (via /sys/class/leds/<device>/trigger). Trigger specific
parameters can appear in /sys/class/leds/<device> once a given trigger is
selected.

write to /sys/devices/platform/i8042/serio0/input/input3/input3::numlock/brightness
0 = off
1 = on
NOTE: MUST be root
"""

import threading
import time

STATSFILE = '/proc/diskstats'
LEDFILE = '/sys/devices/platform/i8042/serio0/input/input3/input3::numlock/brightness'
BLINKRATE = 0.065
DEVICENAME = 2
IOINPROGRESS = 11
LEDON = '1'
LEDOFF = '0'
DEVICE = "sda"

def resetled():
    open(LEDFILE, 'a').write(LEDOFF)

def setled():
    global timer
    if 'timer' in globals():
        if timer.is_alive:
            timer.cancel()
    timer = threading.Timer(BLINKRATE, resetled)
    timer.start()
    open(LEDFILE, 'a').write(LEDON)

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

if __name__ == '__main__':
    resetled()
    while True:
        weightedtime = getioinprogress(DEVICE)
        #print weightedtime
        if weightedtime > 0:
            setled()
        time.sleep(BLINKRATE / 4.0)
