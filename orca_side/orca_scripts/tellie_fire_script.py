#!/usr/bin/env python
import time
import argparse
import xmlrpclib

if __name__=="__main__":
    try:
        print "Attempting to connect to Tellie"
        parser = argparse.ArgumentParser("Usage: orca_script.py <options>")
        parser.add_argument("-c", dest="channel", type=int, default=1, help="Select the TELLIE channel")
        parser.add_argument("-n", dest="pulse_number", type=int, default=1, help="Set the number of pulses")
        parser.add_argument("-d", dest="pulse_delay", type=float, default=0.1, help="Set the delay (ms)")
        parser.add_argument("-t", dest="trigger_delay", type=int, default=0, help="Set the trigger delay")
        parser.add_argument("-w", dest="pulse_width", type=int, default=16383, help="Set the pulse width (intensity)")
        parser.add_argument("-z", dest="pulse_height", type=int, default=16383, help="Set the pulse height (intensity)")
        parser.add_argument("-x", dest="fibre_delay", type=float, default=0, help="Set the individual fibre delay offset")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default="5030", help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))

        try:
#        if True:
            # TODO:
            # Parameter checks need to be performed here
            # But feedback needed for user (e.g. exact pulse number may not be possible)
            #print "ARGS:"
            #print "\tchannel %s" % args.channel
            #print "\tnumber %s" % args.pulse_number
            #print "\tp delay %s" % args.pulse_delay
            #print "\tt delay %s" % args.trigger_delay
            #print "\twidth %s" % args.pulse_width
            #print "\theight %s" % args.pulse_height
            #print "\tf delay %s" % args.fibre_delay
            tellie_server.select_channel(args.channel)
            settings = tellie_server.init_channel(args.channel, args.pulse_number, args.pulse_delay, args.trigger_delay,
                                                  args.pulse_width, args.pulse_height, args.fibre_delay)
            time.sleep(0.1) # just coz
            tellie_server.fire_sequence()
            # These values should come from the init_channel response
            print "Channels", settings["channels"]
            print "Pulse number", settings["pulse_number"]
            print "Pulse delay", settings["pulse_delay"]
            print "Trigger delay", settings["trigger_delay"]
            for c in settings["channel_settings"]:
                print "Channel settings: %s %s" % (c, settings["channel_settings"][c])
        except xmlrpclib.Fault, e:
            # Attempt a safe stop and inform in the return type as to the success?
            tellie_server.stop()
            raise
    except:
        print "Failed to connect to Tellie and fire the fibre"
        raise
