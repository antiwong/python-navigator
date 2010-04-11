#!/usr/bin/python

# power.py

from __future__ import with_statement
from __future__ import division

import sys
import time
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
        power_level1 = None

        with control.pololu(timeout=1) as ctl:
            with open(Input_filename) as input:
                while True:
                    line = input.readline()
                    if line:
                        power_level1, power_level2 = \
                          (int(x) for x in line.split())
                        Logger.info("power_level1 %d, power_level2 %d",
                                    power_level1, power_level2)
                    if power_level1 is None:
                        time.sleep(0.2)
                    else:
                        time.sleep(delay)
                        ctl.set_power(power_level1)
                        time.sleep(delay)
                        ctl.set_power(power_level2)

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
