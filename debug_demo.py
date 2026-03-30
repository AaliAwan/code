# Basic testing and demo file for the debug library
# DEVLIN SAKEY 2024

import debug
# remember you can do this if you want to use a function without specifying the module prefix
# from debug import dprint

# set the debug level - decides what to show of your debug messages
debug.DEBUG_LEVEL = 4
# set the delays level. independent from debug level.
debug.DELAY_LEVEL = 0
#
# the ERROR log - usually you want one of these for when you don't want to write errors in your regular logfiles
# note this file includes a relative path, and uses double backslashes to separate them.
debug.ERROR_LOG="test1\\test2\\test3\\test.err"

# logfile filename
my_logfile = "mylogfile.txt"

debug.dprint(0, debug.DEBUG_LEVEL)
debug.dprint(0,"this will show up at debug level 0")

#Basic debug printing at various levels
debug.dprint(1,"debug level 1 - about to do the thing")
for a in range(10):
    debug.dprint(2, "Debug level 2 - a bit more detail - a=", a)
    debug.dsleep(1,1)
    for b in range(10):
            debug.dprint(3, "Debug level 3 - even more detail - a+b=", a+b)
			# this is if at a certain level of debug, we might want the program to go a little slower
            debug.dsleep(2, 1)
        
# write a timestamped entry into an error log
debug.eprint(0,"error log entry - test check the file", debug.ERROR_LOG)

# write a debug entry to both the screen and a file
debug.fprint(1, my_logfile, "debug entry in a file - ", my_logfile)
# write a debug entry to both the screen and a file
debug.lprint(1, my_logfile, "Timestamped debug entry in a file - ", my_logfile)
# write a debug entry to both the screen and a file - please note this can have different debug levels for file and screen.
# usually you'll want to write to a logfile at some level and only show on the screen at a higher debug level.
debug.bprint(2, 1, my_logfile, "Timestamped debug entry in a logfile and on the screen - ", my_logfile)