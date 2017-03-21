#!/usr/bin/env python
import argparse
import xmlrpclib

if __name__=="__main__":
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
    chan = args.channel
    mean = -1
    rms = -1
    try:
        # TODO:
        # Parameter checks need to be performed here
        # But feedback needed for user (e.g. exact pulse number may not be possible)
	#tellie_server.reset()
        tellie_server.select_channel(args.channel)
        tellie_server.init_channel(args.channel, args.pulse_number, args.pulse_delay, args.trigger_delay,
                                   args.pulse_width, args.pulse_height, args.fibre_delay)
        tellie_server.fire_sequence()
	try: 
	    print "Waiting for sequence to finish..."
            while (mean == -1):
                try:
                    mean, rms, chan = tellie_server.read_pin_sequence()
                except TypeError:
                    mean = None
		if mean == None:
		    mean = -1 
	            rms = -1
                    chan = args.channel

    	except xmlrpclib.Fault, e:
	    # Attempt a safe stop and inform in the return type as to the success?
	    tellie_server.stop()
    except xmlrpclib.Fault, e:
        # Attempt a safe stop and inform in the return type as to the success?
        tellie_server.stop()
    tellie_server.stop()
    print "Chan %s Mean %f RMS %f" %(chan,mean,rms)
        

