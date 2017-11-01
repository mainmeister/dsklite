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

Uses the keyboardleds library
    https://python-keyboardleds.readthedocs.io/en/0.3.3/index.html
"""

import threading
import time
import keyboardleds
import glob

STATSFILE = '/proc/diskstats'
BLINKRATE = 0.065
DEVICENAME = 2
IOINPROGRESS = 11
DEVICE = "mmcblk0"

event_device = glob.glob('/dev/input/by-path/*-event-kbd')[0]
ledkit = keyboardleds.LedKit(event_device)

def resetled():
    ledkit.caps_lock.reset()

def setled():
    global timer
    if 'timer' in globals():
        if timer.is_alive:
            timer.cancel()
    timer = threading.Timer(BLINKRATE, resetled)
    timer.start()
    ledkit.caps_lock.set()

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
