#!/usr/bin/python

# follow.py

from __future__ import with_statement
from __future__ import division

import sys
import os
import stat
import time
import ConfigParser
import logging, logging.config
import control
import angle

Config = ConfigParser.SafeConfigParser()
Config.read('/var/nav/nav.conf')

Input_filename = Config.get('gps_nav', 'output')

# Set up logging:
logging.config.fileConfig(Config.get('follow', 'logging_conf'))
Logger = logging.getLogger('follow')

class gps(object):
    r'''A context manager to read the target heading from the gps file.

    Returns the last heading if no new gps data is available.

    The target heading is -180 to 180 (plus or minus compass variation).

        >>> with gps() as g:
        ...     # g.read() to get target_heading
    '''
    def __init__(self):
        self.f = open(Input_filename)
        size = os.fstat(self.f.fileno())[stat.ST_SIZE]
        if size > 120:
            self.f.seek(-120, os.SEEK_END)      # 120 is just a guess,
                                                # trying to backup to about
                                                # halfway through the next to
                                                # last line.
            self.f.readline()   # This will be a partial line, so discard it.
                                # But it gets us aligned to the start of the
                                # (hopefully) last line.
        self.last_target = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.f.close()

    def read(self):
        line = self.f.readline()
        if line:
            #lat, long, long_radius, north, east, angle_true, angle_magnetic
            self.last_target = float(line.split()[-1])
        return self.last_target

class compass(object):
    #scale_factors = [5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1]
    scale_factors = [5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0]

    def __init__(self, ctl, maxlen=10):
        self.ctl = ctl
        self.maxlen = maxlen
        self.queue = []

    def read(self):
        compass = self.ctl.read_compass()
        Logger.debug("compass %.2f", compass)
        self.queue.insert(0, compass)
        if len(self.queue) > self.maxlen: del self.queue[self.maxlen:]
        ans = sum((fudge * data)
                  for fudge, data in zip(self.scale_factors, self.queue)) \
               / sum(self.scale_factors[:self.maxlen])
        return ans

def run(duration=None, power_level1=None, power_level2=None, fudge=None):
    # power_level 25 doesn't go, 30 does.
    if duration is None:
        duration = Config.getint('follow', 'duration')
    if power_level1 is None:
        power_level1 = Config.getint('follow', 'power_level1')
    if power_level2 is None:
        power_level2 = Config.getint('follow', 'power_level2')
    if fudge is None:
        fudge = Config.getfloat('follow', 'steering_fudge')

    try:
        Logger.info("start: duration %d, power_level1 %d, power_level2 %d, " \
                    "steering fudge %.1f",
                    duration, power_level1, power_level2, fudge)

        with control.pololu(timeout=1) as ctl:
            cp = compass(ctl)
            with gps() as g:
                # wait for first heading:
                while g.read() is None: pass

                ctl.set_range_finder(0)     # look straight ahead

                # preload compass values to get averaging going...
                for i in range(cp.maxlen):
                    cp.read()
                    time.sleep(0.1)

                # Go!
                try:
                    Logger.info("starting vehicle!")
                    power_levels = power_level1, power_level2
                    ctl.set_power(power_level1)
                    time.sleep(0.5)
                    ctl.set_power(power_level2)
                    start = time.time()
                    iterations = 0

                    did_wall = False

                    #print "obstacle_dist actual_heading correction " \
                    #      "processing_time"
                    while time.time() - start < duration:
                        start_tenth = time.time()
                        ctl.set_power(power_levels[iterations & 1])
                        obstacle_dist = ctl.read_distance()

                        # close obstacle detection
                        if not did_wall and obstacle_dist < 500:
                            print >> sys.stderr, "going to wall_following"
                            Logger.info("obstacle encountered at distance %d",
                                        obstacle_dist)
                            wall_follow(cp, ctl, power_levels, start, duration,
                                        1, 200)
                            did_wall = True

                        actual_heading = cp.read()
                        target_heading = g.read()
                        if target_heading == 1000.0:
                            Logger.info("got STOP from gps_nav.py")
                            break

                        # positive is right turn
                        correction = target_heading - actual_heading

                        # correct for small differences around +/-180:
                        if abs(correction) > 180.0:
                            if correction > 0.0: correction -= 360.0
                            else: correction += 360.0

                        ctl.set_steering(correction * fudge)

                        processing_time = time.time() - start_tenth

                        Logger.debug("obstacle_dist %.1f, actual_heading %.1f, "
                                     "correction %.1f, processing_time %.3f",
                                     obstacle_dist, actual_heading, correction,
                                     processing_time)

                        iterations += 1
                        time_left = 0.1 - processing_time
                        if time_left > 0.0: time.sleep(time_left)
                    total_time = time.time() - start
                    Logger.info("done: total time %.2f, iterations %d, "
                                "msec/iteration %.0f",
                                total_time, iterations,
                                (total_time / iterations) * 1000.0)

                finally:
                    # Stop!
                    Logger.info("done: stopping vehicle")
                    ctl.set_power(0)
                    time.sleep(1)
                    ctl.set_power(0)
    except Exception, e:
        print >> sys.stderr, "got exception"
        Logger.exception("%s: %s", e.__class__.__name__, e)
        raise

def wall_follow(cp, ctl, power_levels, start, duration, side=0, distance=200):
    # Stop the car, reposition vehicle at specified distance, use ranger/servo
    # to determine best way to go around obstacle (if side=0), turn the car 90
    # degrees, advance while controlling steering to maintain distance to
    # wall/obstacle.  Exit loop when compass heading is same or close to target
    # heading.
    done = False
    while not done:     # this loops when inside corners are hit
        ctl.set_power(-100)
        time.sleep(1)
        ctl.set_power(0)
        time.sleep(1)
        if side == 0:
            ctl.set_range_finder(-250)     # look to the left
            time.sleep(0.5)
            left_dist = ctl.read_distance()
            ctl.set_range_finder(250)      # look to the right
            time.sleep(0.5)
            right_dist = ctl.read_distance()
            if right_dist > left_dist:
                side = 1    # obstacle on left
            else:
                side = -1   # obstacle on right
            Logger.debug("left_dist %d, right_dist %d, side %d",
                         left_dist, right_dist, side)
        iterations = 0
        actual_heading = cp.read()
        half_new_heading = actual_heading + 25 * side
        new_heading = actual_heading + 70 * side
        Logger.debug("actual_heading %.0f, half_new_heading %.0f, "
                     "new_heading %.0f",
                     actual_heading, half_new_heading, new_heading)
        ctl.set_steering(-500 * side)
        time.sleep(0.5)
        while angle.less(actual_heading * side, half_new_heading * side):
            ctl.set_power(-2 * power_levels[iterations & 1])
            iterations += 1
            time.sleep(0.1)
            actual_heading = cp.read()
        Logger.debug("after backing, actual_heading is %.0f", actual_heading)
        ctl.set_power(0)
        ctl.set_steering(500 * side)
        time.sleep(0.5)
        while angle.less(actual_heading * side, new_heading * side):
            ctl.set_power(power_levels[iterations & 1])
            iterations += 1
            time.sleep(0.1)
            actual_heading = cp.read()
        ctl.set_power(0)
        Logger.debug("after going forward, actual_heading is %.0f",
                     actual_heading)
        ctl.set_range_finder(-500 * side)
        ctl.set_steering(-100 * side)
        time.sleep(2)
        # at this point, the car should be with its side facing the wall
        while time.time() - start < duration:
            start_tenth = time.time()
            ctl.set_power(power_levels[iterations & 1])
            side_dist = ctl.read_distance()
            if side_dist < distance - 20:   # hit corner!
                Logger.info("wall_following hit corner, side_dist is %d",
                            side_dist)
                break
            if side_dist < distance - 20:   # too close
                ctl.set_steering(100 * side)
            elif side_dist > distance + 10: # too far
                ctl.set_steering(-100 * side)
            target_heading = g.read()
            # if car went 20 past target_heading, bail out
            if angle.less(20, (target_heading - actual_heading) * side):
                Logger.info("wall_following done, actual_heading %.0f"
                            "target_heading %.0f",
                            actual_heading, target_heading)
                done = True
                break
            iterations += 1
            time_left = 0.1 - (time.time() - start_tenth)
            if time_left > 0.0: time.sleep(time_left)
            actual_heading = cp.read()
        else:
            Logger.info("wall_following timed out, actual_heading is %.0f",
                        actual_heading)
            done = True
    ctl.set_range_finder(0)     # look straight ahead

def usage():
    print >> sys.stderr, \
          "usage: follow.py [duration [power_level1 [power_level2 [steering_fudge]]]]"
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) > 5 or \
       len(sys.argv) > 1 and sys.argv[1].startswith(('-h', '--h')):
        usage()
    run(*(float(arg) for arg in sys.argv[1:]))
