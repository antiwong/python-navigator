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
        print "compass: %.2f" % compass
        self.queue.insert(0, compass)
        if len(self.queue) > self.maxlen: del self.queue[self.maxlen:]
        ans = sum((fudge * data)
                  for fudge, data in zip(self.scale_factors, self.queue)) \
               / sum(self.scale_factors[:self.maxlen])
        return ans

def run(power_level=30, duration=20, fudge=10.0):
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
                ctl.set_power(power_level)
                time.sleep(0.5)
                start = time.time()

                while time.time() - start < duration:
                    start_tenth = time.time()
                    obstacle_dist = ctl.read_distance()
                    actual_heading = cp.read()
                    print "  actual_heading %.2f" % actual_heading
                    target_heading = g.read()
                    #print "  target_heading %.2f" % target_heading

                    # positive is right turn
                    correction = target_heading - actual_heading

                    #print "  correction1 %.2f" % correction

                    # correct for small differences around +/-180:
                    if abs(correction) > 180.0:
                        if correction > 0.0: correction -= 360.0
                        else: correction += 360.0

                    print "       correction %.2f" % correction

                    ctl.set_steering(correction * fudge)

                    print "  elapsed time %.2f" % (time.time() - start_tenth)

                    time.sleep(0.1)
                print "total time", time.time() - start

            finally:
                # Stop!
                ctl.set_power(0)
                time.sleep(1)
                ctl.set_power(0)

