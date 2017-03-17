#!/usr/bin/env python
import time
import argparse
import xmlrpclib
from snotdaq import logger
from common import parameters as p

if __name__=="__main__":
    try:
        print "Attempting to connect to Tellie server"
        parser = argparse.ArgumentParser("Usage: orca_script.py <options>")
        parser.add_argument("-c", dest="channel", type=int, default=1, help="Select the TELLIE channel [1]")
        parser.add_argument("-n", dest="pulse_number", type=int, default=1, help="Set the number of pulses [1]")
        parser.add_argument("-t", dest="trigger_delay", type=int, default=0, help="Set the trigger delay [0]")
        parser.add_argument("-w", dest="pulse_width", type=int, default=p._max_pulse_width, help="Set the pulse width (intensity)")
        parser.add_argument("-z", dest="pulse_height", type=int, default=p._max_pulse_height, help="Set the pulse height (intensity)")
        parser.add_argument("-x", dest="fibre_delay", type=float, default=0, help="Set the individual fibre delay offset [0]")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default=p._server_port, help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
        _logger = logger.Logger("tellie", args.server, args.port)

        try:
            tellie_server.select_channel(args.channel)
            settings = tellie_server.init_channel(args.channel, args.pulse_number, args.trigger_delay,
                                                  args.pulse_width, args.pulse_height, args.fibre_delay)
            time.sleep(p._short_pause) # just coz
            # These values should come from the init_channel response
            _logger.log(Logger.DEBUG, "Settings as seen by tellie_fire_script.py")
            for key in settings:
                _logger.log(Logger.DEBUG, "%s:\t%s" % (key, settings[key]))
            tellie_server.fire_sequence()
        except xmlrpclib.Fault, e:
            # Attempt a safe stop and inform in the return type as to the success?
            tellie_server.stop()
            raise
    except:
        print "Failed to connect to Tellie and fire the fibre"
        raise
