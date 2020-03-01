#!/usr/bin/env python

import serial
import time
import sys

ser = serial.Serial(port='/dev/ttyUSB0', timeout=10)
messageLen = 5

errorCount = 0

while errorCount < 5:
	ser.write('\0')
	result = ser.read(messageLen)
        print(result)

	if len(result) != messageLen or result[0] != 'R':
		sys.exit(1)

	timestr = time.strftime('%m/%d/%Y %H:%M')
	print('%s,%s\n' % (timestr, result[1:]))
	break
