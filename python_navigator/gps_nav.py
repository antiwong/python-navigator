# gps_nav.py

from __future__ import with_statement

import time
import math
import contextlib
import gps

Output_filename = '/tmp/gps_direction.out'

Earth_radius = 6371000

def run(target_lat, target_long, variation):
    r'''

    variation > 0 for W, < 0 for E.
    '''
    Session = gps.gps()
    print dir(Session)

    long_radius = Earth_radius * math.cos(math.radians(target_lat))
    while True:
        Session.query('o')
        lat = Session.fix.latitude
        long = Session.fix.longitude
        print 'lat', lat, 'long', long
        north = Earth_radius * math.radians(lat - target_lat)
        print 'north', north
        east = long_radius * math.radians(long - target_long)
        print 'east', east
        angle_true = math.degrees(math.atan2(east, north))
        print 'angle, true', angle_true
        print 'angle, magnetic', angle_true + variation
        time.sleep(1)
