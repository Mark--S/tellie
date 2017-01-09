#!/usr/bin/env python
import time
import argparse
import xmlrpclib
from snotdaq import logger

if __name__=="__main__":
    try:
        print "Attempting to connect to Tellie server"
        parser = argparse.ArgumentParser("Usage: orca_script.py <options>")
        parser.add_argument("-c", dest="channel", type=int, default=1, help="Select the TELLIE channel")
        parser.add_argument("-n", dest="pulse_number", type=int, default=1, help="Set the number of pulses")
        parser.add_argument("-t", dest="trigger_delay", type=int, default=0, help="Set the trigger delay")
        parser.add_argument("-w", dest="pulse_width", type=int, default=16383, help="Set the pulse width (intensity)")
        parser.add_argument("-z", dest="pulse_height", type=int, default=16383, help="Set the pulse height (intensity)")
        parser.add_argument("-x", dest="fibre_delay", type=float, default=0, help="Set the individual fibre delay offset")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default="5030", help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
        _logger = logger.Logger("tellie", args.server, args.port)

        try:
            tellie_server.select_channel(args.channel)
            settings = tellie_server.init_channel(args.channel, args.pulse_number, args.trigger_delay,
                                                  args.pulse_width, args.pulse_height, args.fibre_delay)
            time.sleep(0.1) # just coz
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
