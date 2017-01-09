#!/usr/bin/env python
import sys
import argparse
import xmlrpclib
import json as json
from pprint import pprint
from snotdaq import logger 

if __name__=="__main__":
    try:
        #print "Attempting to connect to tellie hardware"
        parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default="5030", help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
        _logger = logger.Logger("tellie", args.server, args.port)
        # Unsure of how to report different errors to Orca
        # Return values?  Seems ugly.

        try:
            channelDict, channels = tellie_server.read_pin_sequence()
            pin = channelDict[channels][0]
            rms = channelDict[channels][1]
            #print "PIN READOUT:", pins, channels
            if pin is None:
                # Sequence is incomplete; handle in return type?
                _logger.Log(Logger.WARNING, "Pin readout returned None")
                sys.exit(1)
            else:
                return pin, rms, channel
        except xmlrpclib.Fault, e:
            print "Error! attempting to exit safely", e
            tellie_server.stop()
    except:
        print "Unable to make connection to Tellie"
