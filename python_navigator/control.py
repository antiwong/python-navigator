# control.py

import serial
import math

Compass_N_midpoint = 575
Compass_E_midpoint = 575

class pololu(object):
    def __init__(self, device='/dev/ttyS3', baud=9600, timeout=0, rtscts=0,
                       debug=False):
        r'''Initialize port.

        timeout in seconds (can be a float).
        '''
        if debug:
            class fake_serial(object):
                def take(self, *args):
                    self.data = ''.join((chr(arg) for arg in args))
                def write(self, data):
                    print "writing:",
                    for byte in data[:-1]:
                        print "0x%02x," % (ord(byte),),
                    if data:
                        print "0x%02x" % (ord(data[-1]),)
                def flush(self):
                    print "flush"
                def read(self, n):
                    return self.data
            self.ser = fake_serial()
        else:
            self.ser = serial.Serial(device, baud, timeout=timeout,
                                     rtscts=rtscts)
            self.write(0xAA) # calibrate pololu serial parameters (baud, etc)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.ser.close()

    def write(self, *args):
        r'''Writes a series of numbers.

        Flushes the bytes to the port.

            >>> s = pololu(debug=True)
            >>> s.write(1,2,3)
            writing: 0x01
            writing: 0x02
            writing: 0x03
            flush
        '''
        for arg in args:
            self.ser.write(chr(arg))
        self.ser.flush()

    def write_servo(self, servo, n):
        r'''Write n to servo.

        n is signed integer: -500 to 500

            >>> s = pololu(debug=True)
            >>> s.write_servo(3, 0)
            writing: 0x84
            writing: 0x03
            writing: 0x70
            writing: 0x2e
            flush
            >>> s.write_servo(0x10, 1)
            writing: 0x84
            writing: 0x10
            writing: 0x74
            writing: 0x2e
            flush
            >>> s.write_servo(0xff, 32)
            writing: 0x84
            writing: 0xff
            writing: 0x70
            writing: 0x2f
            flush
            >>> s.write_servo(0xff, -32)
            writing: 0x84
            writing: 0xff
            writing: 0x70
            writing: 0x2d
            flush
        '''
        n = int(round(n))
        if n < -500: n = -500
        elif n > 500: n = 500
        b2, b1 = divmod(n + 1500, 32)   # 32 is 128/4, 128 is 7 bits
        self.write(0x84, servo, b1 << 2, b2)

    def read_num(self, port):
        r'''Reads 2 bytes as little-endian integer from port.

            >>> s = pololu(debug=True)
            >>> s.ser.take(1, 2)
            >>> s.read_num(0x11)
            writing: 0x90
            writing: 0x11
            flush
            513
        '''
        self.write(0x90, port)
        data = self.ser.read(2)
        if len(data) != 2:
            print "port", port, "short read, wanted 2 bytes, got", len(data), \
                  "bytes"
            if len(data) == 1:
                return ord(data[0])
            return 0
        #while len(data) < 2: data += self.ser.read(2 - len(data))
        return ord(data[0]) + (ord(data[1]) << 8)

    def set_power(self, level):
        self.write_servo(3, -level)
        self.power_level = level

    def set_steering(self, direction):
        self.write_servo(4, -direction)
        self.direction = direction

    def set_range_finder(self, rf_direction):
        self.write_servo(5, rf_direction)
        self.rf_direction = rf_direction

    def read_distance(self):
        self.distance = self.read_num(2)
        return self.distance

    def read_compass(self):
        east = self.read_num(0) - Compass_E_midpoint
        north = self.read_num(1) - Compass_N_midpoint
        #print "port 0 (east) = %d, port 1 (north) = %d" % (east, north)
        self.heading = math.degrees(math.atan2(east, north))
        #print "compass heading", self.heading
        return self.heading

if __name__ == "__main__":
    import doctest
    doctest.testmod()
