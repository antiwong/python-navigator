#!/usr/bin/python

# follow.py

from __future__ import with_statement
from __future__ import division

import sys
import os
import stat
import time
import control

Input_filename = '/tmp/gps_direction.out'

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
        print "compass: %.2f" % compass
        self.queue.insert(0, compass)
        if len(self.queue) > self.maxlen: del self.queue[self.maxlen:]
        ans = sum((fudge * data)
                  for fudge, data in zip(self.scale_factors, self.queue)) \
               / sum(self.scale_factors[:self.maxlen])
        return ans

def run(power_level1=30, power_level2=25, duration=20, fudge=5.0):
    # power_level 25 doesn't go, 30 does.
    with control.pololu(timeout=1) as ctl:
        cp = compass(ctl)
        with gps() as g:
            # wait for first heading:
            while g.read() is None: pass

            # preload compass values to get averaging going...
            for i in range(cp.maxlen):
                cp.read()
                time.sleep(0.1)

            # Go!
            try:
                power_levels = power_level1, power_level2
                ctl.set_power(power_level1)
                time.sleep(0.5)
                ctl.set_power(power_level2)
                start = time.time()
                iterations = 0

                print "obstacle_dist actual_heading correction " \
                      "processing_time"
                while time.time() - start < duration:
                    ctl.set_power(power_levels[iterations & 1])
                    start_tenth = time.time()
                    obstacle_dist = ctl.read_distance()
                    actual_heading = cp.read()
                    target_heading = g.read()
                    if target_heading == 1000.0:
                        break

                    # positive is right turn
                    correction = target_heading - actual_heading

                    # correct for small differences around +/-180:
                    if abs(correction) > 180.0:
                        if correction > 0.0: correction -= 360.0
                        else: correction += 360.0

                    ctl.set_steering(correction * fudge)

                    processing_time = time.time() - start_tenth

                    print "%6.1f %6.1f %6.1f %5.3f" % \
                            (obstacle_dist, actual_heading, correction,
                             processing_time)

                    iterations += 1
                    time_left = 0.1 - processing_time
                    if time_left > 0.0: time.sleep(time_left)
                total_time = time.time() - start
                print "total time", total_time, \
                      "iterations", iterations, \
                      "time/iteration", total_time / iterations

            finally:
                # Stop!
                ctl.set_power(0)
                time.sleep(1)
                ctl.set_power(0)

def usage():
    print >> sys.stderr, \
          "usage: follow.py [power_level1 [power_level2 [duration [steering_fudge]]]]"
    print >> sys.stderr, \
          "       defaults: 30 20 20 5.0"
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) > 5 or sys.argv[1].startswith(('-h', '--h')): usage()
    run(*(float(arg) for arg in sys.argv[1:]))
