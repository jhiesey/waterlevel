#!/usr/bin/env python

import subprocess
import serial
import time

badLow = 30
badHigh = 500
fullOffset = 49 # this many cm is full

ser = serial.Serial(port='/dev/ttyUSB0', timeout=10)
messageLen = 6

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

	rawLevel = float(result[1:]) / 10
	if rawLevel == badLow or rawLevel == badHigh:
		errorCount += 1
		continue

	level = rawLevel - fullOffset
	timestr = time.strftime('%m/%d/%Y %H:%M')
	outfile.write('%s,%s\n' % (timestr, level))
	break

outfile.close()

subprocess.call(['rsync', datapath, 'tunnel@hiesey.com:~/waterlevel.csv'])
