#!/usr/bin/env python
import sys
import argparse
import xmlrpclib
import json as json
from pprint import pprint
from snotdaq import logger 
from common import parameters as p

if __name__=="__main__":
    try:
        #print "Attempting to connect to tellie hardware"
        parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default=p._server_port, help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
        _logger = logger.Logger("tellie", args.server, args.port)
        # Unsure of how to report different errors to Orca
        # Return values?  Seems ugly.

        try:
            pin = None
            while (pin == None):
                try:
                    pin, rms, channel = tellie_server.read_pin_sequence()
                except TypeError:
                    pin = None
            return pin, rms, channel
        except xmlrpclib.Fault, e:
            print "Error! attempting to exit safely", e
            tellie_server.stop()
    except:
        print "Unable to make connection to Tellie"
