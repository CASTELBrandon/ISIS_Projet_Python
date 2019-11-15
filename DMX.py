import time
import serial
import struct

ser = serial.Serial(port='/dev/ttyAMA0', baudrate=250000, parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                    timeout=None)

universize = 24
list = [0] * universize
list[0] = 0
list[1] = 255
list[2] = 255
list[3] = 255
list[4] = 255
list[5] = 0
print(list)
master = 255


def dmx():
    global universize
    global list
    global master
    for j in range(0, universize, 1):
        ser.write(struct.pack('<H', list[j] / 255 * master))
        print(j)


while 1:
    ser.send_break(duration=0.001)
    ser.write(struct.pack('<H', 0))
    dmx()