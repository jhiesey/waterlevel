#!/usr/bin/env python

import serial
import time

ser = serial.Serial(port='/dev/ttyUSB0', timeout=10)
messageLen = 5

errorCount = 0

while errorCount < 5:
	ser.write('\0')
	result = ser.read(messageLen)

	if len(result) != messageLen or result[0] != 'R':
		errorCount += 1
		ser.read(100) # Drain buffer
		continue

	timestr = time.strftime('%m/%d/%Y %H:%M')
	print('%s,%s\n' % (timestr, result[1:]))
	break
