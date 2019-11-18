#!/usr/bin/env python

## Check if Serial0 is deleted in /boot/cmdline.txt
## TX Serial0 is on pin 8
## Use 2-5% of cpu (Pi2) while running

import time
import serial
#import pause as p
import struct
import threading

# Serial Setup for DMX transmission
ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate = 250000,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0   
   )

lock = threading.RLock()

# Initialize variable
universize = 513
dmxbuffer = [0] * universize

# Send Channels through DMX
def dmxfonction(dmxbuffer):
    with lock:
        while True:
            global universize
            tosend=dmxbuffer
            ser.break_condition = True
            time.sleep(0.001)               # Send Break    
            ser.break_condition = False
            ser.write(struct.pack('<B', 0)) # Start Code
            for i in range(0, universize, 1):
                ser.write(struct.pack('<B', tosend[i]))

# Test values
dmxbuffer[0] = 255     # Rouge
dmxbuffer[1] = 255     # Vert
dmxbuffer[2] = 255     # Blue
dmxbuffer[3] = 255     # Blanc
dmxbuffer[4] = 255     # Master
dmxbuffer[5] = 0
# Main Loop

processThread = threading.Thread(target=dmxfonction, args=(dmxbuffer,))
processThread.start()

while True:
    with lock:
        dmxbuffer[4] = 255     # Master
