# control.py

import serial

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
            >>> s.write_servo(0xFF, 32)
            writing: 0x84
            writing: 0xff
            writing: 0x70
            writing: 0x2f
            flush
            >>> s.write_servo(0xFF, -32)
            writing: 0x84
            writing: 0xff
            writing: 0x70
            writing: 0x2d
            flush
        '''
        b2, b1 = divmod(n + 1500, 32)   # 32 is 128/4, 128 is 7 bits
        self.write(0x84, servo, b1 << 2, b2)

    def read_num(self):
        r'''Reads 2 bytes as little-endian integer.

            >>> s = pololu(debug=True)
            >>> s.ser.take(1, 2)
            >>> s.read_num()
            513
        '''
        ans = 0
        data = self.ser.read(2)
        while len(data) < 2: data += self.ser.read(2 - len(data))
        return ord(data[0]) + (ord(data[1]) << 8)

    def set_power(self, level):
        self.write_servo(0x03, level)
        self.power_level = level

    def set_steering(self, direction):
        self.write_servo(0x04, direction)
        self.direction = direction

    def set_range_finder(self, rf_direction):
        self.write_servo(0x05, rf_direction)
        self.rf_direction = rf_direction

    def read_distance(self):
        self.write(0x90, 0x02)
        self.distance = self.read_le(2)
        return self.distance

if __name__ == "__main__":
    import doctest
    doctest.testmod()
