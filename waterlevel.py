#!/usr/bin/env python3

import argparse
import subprocess
import serial
import time

parser = argparse.ArgumentParser(description='Read water level')
parser.add_argument('--test', action='store_true')
args = parser.parse_args()

badLow = 300 # low reading error mm
badHigh = 5000 # high reading error mm

fullOffset = 49 # this many cm is full

ser = serial.Serial(port='/dev/ttyUSB0', timeout=10)
messageLen = 6

datapath = '/home/pi/waterlevel/data.csv'
errorCount = 0

while errorCount < 5:
	ser.write(b'\0')
	result = ser.read(messageLen).decode('ascii')

	if len(result) != messageLen or result[0] != 'R':
		print('Got bad serial data!')
		errorCount += 1
		ser.read(100) # Drain buffer
		continue

	rawLevel = int(result[1:])
	if rawLevel == badLow or rawLevel == badHigh:
		print('Got invalid reading (mm):', rawLevel)
		errorCount += 1
		continue

	level = rawLevel / 10 - fullOffset
	timestr = time.strftime('%m/%d/%Y %H:%M')
	outLine = f'{timestr},{level:.1f}\n'
	if args.test:
		print(outLine)
	else:
		outfile = open(datapath, 'a')
		outfile.write(outLine)
		outfile.close()

		subprocess.call(['rsync', datapath, 'tunnel@hiesey.com:~/waterlevel.csv'])
	break
