#!/usr/bin/env python3

import argparse
import subprocess
import serial
import time
import struct
import re
import sys

parser = argparse.ArgumentParser(description='Read water level')
parser.add_argument('--port', default='/dev/ttyUSB0')
parser.add_argument('--test', action='store_true')
args = parser.parse_args()

"""
Non-default radio settings

House (house_modem.xpro):
ID: 3ABC
SH: 13A200
SL: 40661DAC
DD: 40000
AP: 2

Tank (tank_modem.xpro):
ID: 3ABC
SH: 13A200
SL: 408950ED
DD: 40000
AP: 2
D1: 2
PR: 7FFF
"""

DATA_PATH = '/home/pi/waterlevel/data.csv'
REMOTE_ADDR = bytes.fromhex('0013A200408950ED') # MAC address of tank radio
ZERO_OFFSET = 1024 / 10.0
SLOPE_PSI_PER_COUNT = 6.5 / 1024 # Theoretical: 6.25 / 1024
SLOPE_CM_PER_COUNT = SLOPE_PSI_PER_COUNT * 70.307
TANK_FULL_HEIGHT_CM = 173.0 # Theoretical: about 170 (plus zero pressure offset)
NUM_READINGS_AVERAGE = 10

def escape_byte(match):
	return b'\x7d' + (match.group(0)[0] ^ 0x20).to_bytes(1, 'big')

def send_request(ser, frame_id):
	frame_data = struct.pack('!BB8sHB2s', 0x17, frame_id, REMOTE_ADDR, 0xFFFE, 0, b'IS')

	checksum = 0xFF
	for byte in frame_data:
		checksum -= byte
		if checksum < 0:
			checksum += 0x100

	framed_data = len(frame_data).to_bytes(2, 'big') + frame_data + checksum.to_bytes(1, 'big')

	packet_data = b'\x7e' + re.sub(b'[\x7e\x7d\x11\x13]', escape_byte, framed_data)
	if args.test:
		print('SEND:', packet_data.hex())
	ser.write(packet_data)

def read_escaped_bytes(ser, desired_length):
	out = b''

	while len(out) < desired_length:
		b = ser.read(1)
		if args.test:
			print('RECEIVE:', b.hex())

		if b == b'':
			raise Exception('Short read')
		if b == b'\x7e':
			raise Exception('Unexpected start byte')

		if b == b'\x7d':
			b2 = ser.read(1)
			if args.test:
				print('RECEIVE:', b2.hex())
			if b2 == b'':
				raise Exception('Short read')
			out += (b2[0] ^ 0x20).to_bytes(1, 'big')
		else:
			out += b

	return out

def get_response(ser, expected_frame_id):
	while True:
		# Find delimiter
		while True:
			b = ser.read(1)
			if args.test:
				print('RECEIVE:', b.hex())
			if b == b'':
				raise Exception('No response from remote radio')
			if b == b'\x7e':
				break

		[packet_len] = struct.unpack('!H', read_escaped_bytes(ser, 2))

		frame_data = read_escaped_bytes(ser, packet_len + 1)

		checksum = 0
		for byte in frame_data:
			checksum += byte
			if checksum > 0xFF:
				checksum -= 0x100

		if checksum != 0xFF:
			raise Exception('Bad checksum')

		[frame_type, frame_id, addr, reserved, command, status] = struct.unpack_from('!BB8sH2sB', frame_data, 0)
		# Find the frame we want
		if frame_type != 0x97 or frame_id != expected_frame_id:
			continue

		# Check for error
		if status == 0x4:
			raise Exception('Failed to get response from tank radio')

		data_len = packet_len - 15

		# Sanity check
		if addr != REMOTE_ADDR or command != b'IS' or status != 0x0 or data_len != 6:
			raise Exception('Bad packet format')

		[sample_sets, digital_mask, analog_mask, sample] = struct.unpack_from('!BHBH', frame_data, 15)

		# Sanity check
		if sample_sets != 1 or digital_mask != 0 or analog_mask != 2:
			raise Exception('Unexpected set of sampled channels')

		return TANK_FULL_HEIGHT_CM - (sample - ZERO_OFFSET) * SLOPE_CM_PER_COUNT

next_frame_id = 1

def get_reading():
	global next_frame_id
	frame_id = next_frame_id
	next_frame_id += 1
	if next_frame_id > 255:
		next_frame_id = 1

	ser = serial.Serial(port=args.port, baudrate=9600, timeout=10)
	send_request(ser, frame_id)
	return get_response(ser, frame_id)

def main():
	level = 0
	try:
		for i in range(NUM_READINGS_AVERAGE):
			level += get_reading()
	except Exception as ex:
		print('Failed to get reading!', ex)
		sys.exit()

	level = level / NUM_READINGS_AVERAGE
	timestr = time.strftime('%m/%d/%Y %H:%M')
	outLine = f'{timestr},{level:.1f}\n'
	if args.test:
		print(outLine)
	else:
		outfile = open(DATA_PATH, 'a')
		outfile.write(outLine)
		outfile.close()

		subprocess.call(['rsync', DATA_PATH, 'tunnel@hiesey.com:~/waterlevel.csv'])

if __name__ == '__main__':
	main()
