#!/usr/bin/env python

import os
import time

# configurable pieces
HOLIDAY_FILE = './config/holidays.conf'
ADAMUS_PROFILE = '~/.profile.ADAMUS'

# read in holidays
with open(HOLIDAY_FILE) as f:
    holidays = {line.strip().split()[0]: 1 for line in f if line.strip()}

# get current date and time
mon, day, yr = time.localtime()[:3]
mon += 1
yr += 1900
today = "{:02d}/{:02d}/{:04d}".format(mon, day, yr)

# run command based on whether it's a holiday or not
cmd = " ".join(os.sys.argv[1:])
if today in holidays:
    print("[REMINDER] {}: today ({}) is a holiday".format(time.ctime(), today))
    os.system("source {}; {}".format(ADAMUS_PROFILE, cmd))
else:
    print("{}: RUNNING...".format(time.ctime()))
    os.system("source {}; {}".format(ADAMUS_PROFILE, cmd))

print("\n\n")
