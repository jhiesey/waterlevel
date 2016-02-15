#!/usr/bin/env python

import subprocess
import serial
import time

ser = serial.Serial(port='/dev/ttyUSB0', timeout=10)
messageLen = 5

datapath = '/home/pi/waterlevel/data.csv'
outfile = open(datapath, 'a')
errorCount = 0

while errorCount < 5:
	ser.write('\0')
	result = ser.read(messageLen)

	if len(result) != messageLen or result[0] != 'R':
		errorCount += 1
		ser.read(100) # Drain buffer
		continue

	timestr = time.strftime('%m/%d/%Y %H:%M')
	outfile.write('%s,%s\n' % (timestr, result[1:]))
	break

outfile.close()

subprocess.call(['rsync', datapath, 'jhiesey@hiesey.com:~/waterlevel/data.csv'])
