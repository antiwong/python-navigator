#!/usr/bin/python

# gps_nav.py

from __future__ import with_statement

import sys
import time
import math
import contextlib
import logging, logging.config
import gps

# lat long long_radius north east angle_true angle_magnetic
Output_filename = '/var/nav/gps_direction.out'

Earth_radius = 6371000

# Set up logging:
logging.config.fileConfig('/var/nav/logging.conf')
Logger = logging.getLogger('gps_nav')

def run(filename='/var/nav/gps_waypoints', variation=2, threshold=5):
    r'''

    variation > 0 for W, < 0 for E.
    '''
    Logger.info("started with: %r, variation=%r, threshold=%r",
                filename, variation, threshold)
    try:
        with open(filename) as waypoints:
            with contextlib.closing(gps.gps()) as session:
                with open(Output_filename, 'wt', 1) as outfile:
                    for waypoint in waypoints:
                        latitude, longitude = \
                          (float(x) for x in waypoint.split())
                        Logger.info("new waypoint: %s, %s", latitude, longitude)
                        navigate_to(latitude, longitude, session, outfile,
                                    variation, threshold)
                    Logger.info("done!")
                    outfile.write("1000.0\n")       # signal to stop
    except Exception, e:
        Logger.exception("%s: %s", e.__class__.__name__, e)
        raise

def navigate_to(target_lat, target_long, session, outfile, variation,
                threshold):
    # Radius of the circle of longitude at the target latitude.
    long_radius = Earth_radius * math.cos(math.radians(target_lat))
    Logger.debug("Earth_radius %.0f, long_radius %.0f",
                 Earth_radius, long_radius)

    #print >> outfile, "lat, long, long_radius, " \
    #                  "north, east, angle_true, angle_magnetic"

    while True:
        session.query('o')

        lat = session.fix.latitude
        long = session.fix.longitude
        Logger.debug("got lat %.6f, long %.6f", lat, long)
        #print 'lat', lat, 'long', long

        north, east, angle_true, angle_magnetic = \
          calc_angle(target_lat, target_long, variation, long_radius,
                     lat, long)

        Logger.debug("north %.1f, east %.1f, true %.1f, magnetic %.1f",
                     north, east, angle_true, angle_magnetic)
        #print 'north', north
        #print 'east', east
        #print 'angle, true', angle_true
        #print 'angle, magnetic', angle_magnetic

        if max(abs(north), abs(east)) < threshold:
            print "waypoint", target_lat, target_long, "reached, north", \
                  north, "east", east
            break

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
          "usage: gps_nav.py [waypoint_filename [variation [threshold]]]"
    print >> sys.stderr, \
          "       variation is > 0 for W, < 0 for E"
    print >> sys.stderr, \
          "       defaults: /var/nav/gps_waypoints 2 5"
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) > 4 or \
       len(sys.argv) > 1 and sys.argv[1].startswith(('-h', '--h')):
        usage()
    if len(sys.argv) == 4:
        run(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    elif len(sys.argv) == 3:
        run(sys.argv[1], float(sys.argv[2]))
    elif len(sys.argv) == 2:
        run(sys.argv[1])
    else:
        run()
