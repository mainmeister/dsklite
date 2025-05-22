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
import os
import sys

STATSFILE = '/proc/diskstats'
LEDFILE = '/sys/devices/platform/i8042/serio0/input/input3/input3::numlock/brightness'
BLINKRATE = 0.065
DEVICENAME = 2
IOINPROGRESS = 11
LEDON = '1'
LEDOFF = '0'
DEVICE = "sda"

timer = None  # Initialize timer to None

def resetled():
    try:
        with open(LEDFILE, 'w') as f:
            f.write(LEDOFF)
    except (IOError, OSError) as e:
        # Log error if LEDFILE cannot be written.
        # Continue execution as the main loop will retry LED operations.
        # This assumes the issue might be transient (e.g., permissions temporarily changed).
        sys.stderr.write(f"Error writing to LEDFILE '{LEDFILE}' in resetled: {e}\n")

def setled():
    global timer
    # Cancel any existing timer to ensure the LED-off action is correctly timed
    # from this 'setled' call.
    if timer is not None and timer.is_alive():
        timer.cancel()
    
    try:
        # Start a timer to call resetled, which will turn the LED off after BLINKRATE.
        timer = threading.Timer(BLINKRATE, resetled)
        timer.start()
    except Exception as e: # Broad exception for timer start issues
        # Log error if the timer cannot be started.
        # This might mean the LED blinking behavior is compromised.
        # Continue execution, as disk activity monitoring is still valuable.
        sys.stderr.write(f"Error starting timer in setled: {e}\n")
        # Potentially attempt to re-initialize or handle, for now, just log

    try:
        # Turn the LED on.
        with open(LEDFILE, 'w') as f: # Changed 'a' to 'w' for overwriting
            f.write(LEDON)
    except (IOError, OSError) as e:
        # Log error if LEDFILE cannot be written.
        # Continue execution as the main loop will retry LED operations on next activity.
        sys.stderr.write(f"Error writing to LEDFILE '{LEDFILE}' in setled: {e}\n")

def getstat(device):
    try:
        with open(STATSFILE, 'r') as f:
            stats = f.readlines()
        for stat_line in stats: # Renamed stat to stat_line to avoid conflict
            lstat = stat_line.split()
            # Check if the line is long enough and matches the target device.
            if len(lstat) > DEVICENAME and lstat[DEVICENAME] == device:
                return lstat
    except (IOError, OSError) as e:
        # Log error if STATSFILE cannot be read. This is a non-critical error for a single read attempt.
        # Recovery: Return None, getioinprogress will then return 0, indicating no activity.
        # The main loop will continue and retry reading on the next iteration.
        sys.stderr.write(f"Error reading STATSFILE '{STATSFILE}': {e}\n")
    return None # Return None on error or if device not found

def getioinprogress(device):
    stat_data = getstat(device) # Renamed stat to stat_data
    if stat_data and len(stat_data) > IOINPROGRESS:
        try:
            return int(stat_data[IOINPROGRESS])
        except ValueError as e:
            # Log error if the I/O progress value is not a valid integer.
            # Recovery: Return 0, treating malformed data as no current I/O activity.
            # This prevents the application from crashing due to unexpected file content.
            sys.stderr.write(f"Error converting IOINPROGRESS to int for device '{device}': {e}\nData: {stat_data}\n")
            return 0
    # If stat_data is None (due to read error in getstat) or not structured as expected,
    # or if IOINPROGRESS index is out of bounds.
    # Recovery: Return 0, indicating no I/O activity detected or data unavailable.
    # This is a safe default, as it implies no need to blink the LED.
    return 0

if __name__ == '__main__':
    try:
        # Fork the process to run the LED monitoring in the background (child process).
        pid = os.fork()
    except OSError as e:
        # Forking is essential for the daemon-like behavior of this script.
        # If fork fails, the script cannot run as intended (e.g., detaching from terminal).
        # Recovery: Log a critical error and exit, as the core functionality is impaired.
        sys.stderr.write(f"Error: Failed to fork process: {e}\n")
        sys.exit(1) # Exit if fork fails

    if pid == 0:  # Child process
        # Ensure the LED is in a known off state when the child process starts.
        resetled() # Ensure LED is off at start
        while True:
            weightedtime = getioinprogress(DEVICE)
            if weightedtime > 0:
                setled()
            # No need for an else to call resetled() here, as setled() schedules resetled() via timer
            time.sleep(BLINKRATE / 4.0)
    else: # Parent process
        sys.exit(0) # Parent exits immediately
