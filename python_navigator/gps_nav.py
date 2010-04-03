#!/usr/bin/python

# gps_nav.py

from __future__ import with_statement

import sys
import time
import math
import contextlib
import gps

# lat long long_radius north east angle_true angle_magnetic
Output_filename = '/tmp/gps_direction.out'

Earth_radius = 6371000

def run(filename='/tmp/gps_waypoints', variation=2):
    r'''

    variation > 0 for W, < 0 for E.
    '''
    with open(filename) as waypoints:
        with contextlib.closing(gps.gps()) as session:
            with open(Output_filename, 'wt', 1) as outfile:
                for waypoint in waypoints:
                    latitude, longitude = (float(x) for x in waypoint.split())
                    navigate_to(latitude, longitude, session, outfile,
                                variation)
                outfile.write("1000.0\n")       # signal to stop

def navigate_to(target_lat, target_long, session, outfile, variation):
    # Radius of the circle of longitude at the target latitude.
    long_radius = Earth_radius * math.cos(math.radians(target_lat))
    #print "long_radius", long_radius

    while True:
        session.query('o')

        lat = session.fix.latitude
        long = session.fix.longitude
        #print 'lat', lat, 'long', long

        north, east, angle_true, angle_magnetic = \
          calc_angle(target_lat, target_long, variation, long_radius,
                     lat, long)

        #print 'north', north
        #print 'east', east
        #print 'angle, true', angle_true
        #print 'angle, magnetic', angle_magnetic

        print >> outfile, lat, long, long_radius, \
                          north, east, angle_true, angle_magnetic

        time.sleep(1)

def calc_angle(target_lat, target_long, variation, long_radius, lat, long):
    # distance in meters north to target (< 0 if target is south)
    north = Earth_radius * math.radians(target_lat - lat)

    # distance in meters east to target (< 0 if target is west)
    east = long_radius * math.radians(target_long - long)

    # True heading to target. -180 to 180
    angle_true = math.degrees(math.atan2(east, north))

    # Magnetic heading to target. -180 to 180
    angle_magnetic = angle_true + variation

    return north, east, angle_true, angle_magnetic

def usage():
    print >> sys.stderr, \
          "usage: gps_nav.py [waypoint_filename [variation]]"
    print >> sys.stderr, \
          "       variation is > 0 for W, < 0 for E"
    print >> sys.stderr, \
          "       defaults: /tmp/gps_waypoints 2"
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) > 3 or sys.argv[1].startswith(('-h', '--h')): usage()
    if len(sys.argv) == 3:
        run(sys.argv[1], float(sys.argv[2]))
    elif len(sys.argv) == 2:
        run(sys.argv[1])
    else:
        run()
