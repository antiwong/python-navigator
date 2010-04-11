#!/usr/bin/python

# power.py

from __future__ import with_statement
from __future__ import division

import sys
import time
import os
import ConfigParser
import logging, logging.config
import control

Config = ConfigParser.SafeConfigParser()
Config.read('/var/nav/nav.conf')

Input_filename = Config.get('power', 'input')

# Set up logging:
logging.config.fileConfig(Config.get('power', 'logging_conf'))
Logger = logging.getLogger('power')

def run():
    # power_level 25 doesn't go, 30 does.
    try:
        delay = Config.getfloat('power', 'delay')
        Logger.info("start: delay %.3f", delay)

        with control.pololu(timeout=1) as ctl:
            if not os.exists(Input_filename):
                open(Input_filename, 'w').close()
            with open(Input_filename) as input:
                line = None
                # read to EOF:
                for line in input.readline(): pass
                # wait for first line:
                while not line:
                    time.sleep(0.2)
                    line = input.readline()
                while True:
                    if line:
                        power_level1, power_level2 = \
                          (int(x) for x in line.split())
                        Logger.info("power_level1 %d, power_level2 %d",
                                    power_level1, power_level2)
                    time.sleep(delay)
                    ctl.set_power(power_level1)
                    time.sleep(delay)
                    ctl.set_power(power_level2)
                    line = input.readline()

    except Exception, e:
        print >> sys.stderr, "got exception"
        Logger.exception("%s: %s", e.__class__.__name__, e)
        raise

    finally:
        # Stop!
        Logger.info("done: stopping vehicle")
        ctl.set_power(0)
        time.sleep(1)
        ctl.set_power(0)

def usage():
    print >> sys.stderr, "usage: power.py"
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) > 1: usage()
    run()
