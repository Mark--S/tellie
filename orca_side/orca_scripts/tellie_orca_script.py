#!/usr/bin/env python
import argparse
import xmlrpclib
import time
from common import parameters as p

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="pulse_delay", type=float, help="Set the delay (ms)")
    parser.add_argument("-f", dest="fibre", type=int, help="Select the fibre")
    parser.add_argument("-n", dest="number", type=int, help="Set the number of pulses")
    parser.add_argument("-i", dest="intensity", type=int, help="Set the pulse width (intensity)")
    parser.add_argument("-t", dest="trigger_delay", type=float, help="Set the trigger delay")
    parser.add_argument("-x", dest="fibre_delay", type=float, help="Set the individual fibre delay offset")
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    args = parser.parse_args()

    # TODO - Have the server proxy string interpreted from the parameters file tellie.cfg
    tellie_server= xmlrpclib.ServerProxy('http://localhost:5030', allow_none = True)
    try:
        print tellie_server.select_channel(10)
        print tellie_server.set_pulse_height(p._max_pulse_height)
        print tellie_server.set_pulse_width(0)
        print tellie_server.set_fibre_delay(0)
        print tellie_server.set_trigger_delay(0)
        print tellie_server.set_pulse_delay(1.0)
        print tellie_server.set_pulse_number(100)
        print tellie_server.fire_sequence()
        time.sleep(p._long_pause)
        time.sleep(p._long_pause)
#        print tellie_server.fire_single()
        print "reading..."
        pin = None
        while (pin == None):
            try:
                pin, rms, chan = tellie_server.read_pin_sequence()
            except TypeError:
                pin = None
        print pin, rms, chan
        print "DONE"
    except xmlrpclib.Fault, e:
        tellie_server.safe_exit()
        print "ERROR:", e
        raise
