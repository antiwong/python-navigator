# Introduction #

The Pololu Maestro shall be controlled with the Compact Protocol, as specified in the online manual:
http://www.pololu.com/docs/0J40/all

# Details #

Start with Python in interactive mode and open the serial port:
```
>>> import serial
>>> ser = serial.Serial('/dev/ttyS3')
>>> ser.write(chr(0xAA))
>>> ser.flush()
```
Note: ttyS3 may change to ttyACM when USB drivers for ARM get figured out. 0xAA is for the auto-baud detector and needs only be sent once.

To control the throttle
```
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x70)+chr(0x2E))  # 0x2E70 = 0b010.1110.111.0000 = 6000 -> 1500us = zero power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x08)+chr(0x27))  # 0x2708 = 0b010.0111.000.1000 = 5000 -> 1250us = 50% forward power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x20)+chr(0x1F))  # 0x1F20 = 0b001.1111.010.0000 = 4000 -> 1000us = 100% forward power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x70)+chr(0x2E))  # 0x2E70 = 0b010.1110.111.0000 = 6000 -> 1500us = zero power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x58)+chr(0x36))  # 0x3658 = 0b011.0110.101.1000 = 7000 -> 1750us = 50% backward power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x40)+chr(0x3D))  # 0x3D40 = 0b011.1110.100.0000 = 8000 -> 2000us = 100% backward power
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x70)+chr(0x2E))  # 0x2E70 = 0b010.1110.111.0000 = 6000 -> 1500us = zero power
```

To control the steering wheels, replace 0x03 with 0x04 in the second character.
To control the ranger servo, replace 0x03 with 0x05 in the second character.

If we are not interested in controlling with 1024 PWM levels, we can opt for 32 steps of the full range (32us precision), and we can simplify the funky 3bit-4bit-3bit-4bit formula with:
```
>>> speed=0
>>> ser.write(chr(0x84)+chr(0x03)+chr(0x70)+chr(0x2E-speed))
```
Where speed can be set from -16 (backward) to 15 (forward). It was found that speed=2 is the minimum value to make the wheels spin.

To read analog values from the ranger and both compass' channels, we must first use the Maestro Control Center under MS Windows and set channels 0, 1 and 2 to inputs. Supposedly, this setting sticks across powerdown/powerup. Then, read it from Python with these commands.
```
>>> ser.write(chr(0x90)+chr(0))
>>> compassA=ser.read()+ser.read()*256
>>> ser.flush()
>>> ser.write(chr(0x90)+chr(1))
>>> compassB=ser.read()+ser.read()*256
>>> ser.flush()
>>> ser.write(chr(0x90)+chr(2))
>>> range=ser.read()+ser.read()*256
>>> ser.flush()
```
Note that the funky 7 bit formula does not apply to decoding analog readings.