# follow.py

from __future__ import with_statement
from __future__ import division

import os
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
        self.f.seek(0, os.SEEK_END)
        self.last_target = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.f.close()

    def read(self):
        line = self.f.readline()
        if line:
            lat, long, long_radius, north, east, angle_true, angle_magnetic = \
              line.split()
            self.last_target = float(angle_magnetic)
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
        print "compass:", compass
        self.queue.insert(0, compass)
        if len(self.queue) > self.maxlen: del self.queue[self.maxlen:]
        ans = sum((fudge * data)
                  for fudge, data in zip(self.scale_factors, self.queue)) \
               / sum(self.scale_factors[:self.maxlen])
        return ans

def run(fudge=10.0, duration=20):
    with control.pololu() as ctl:
        cp = compass(ctl)
        with gps() as g:
            # wait for first heading:
            while g.read() is None: pass

            # preload compass values to get averaging going...
            for i in range(cp.maxlen):
                cp.read()
                time.sleep(0.1)

            # Go!
            start = time.time()
            ctl.set_power(64)
            time.sleep(0.5)

            while time.time() - start < duration:
                obstacle_dist = ctl.read_distance()
                actual_heading = cp.read()
                print "actual_heading", actual_heading
                target_heading = g.read()
                print "target_heading", target_heading

                # positive is right turn
                correction = target_heading - actual_heading

                print "correction1", correction

                # correct for small differences around +/-180:
                if abs(correction) > 180.0:
                    if correction > 0.0: correction -= 360.0
                    else: correction += 360.0

                print "correction2", correction

                ctl.set_steering(correction * fudge)

                time.sleep(0.1)

            # Stop!
            ctl.set_power(0)
