<h1>Drive light emulated on keyboard num lock</h1>
I have a laptop that is lacking a drive activity led. I don't really use the num lock so I thought it could be used to show drive activity.

Written in python 2.7.

Must run as root to be able to write to the /sys/devices/platform/i8042/serio0/input/input3/input3::numlock/brightness file.

Reads the drive's "I/Os currently in progress" from the /proc/diskstats pseudo file.

Uses the threading module to schedule reads. This allows a very efficient design.
 