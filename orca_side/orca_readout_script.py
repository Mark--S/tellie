#!/usr/bin/env python
import sys
import argparse
import xmlrpclib
from common import parameters as p

if __name__=="__main__":
    parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
    parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
    parser.add_argument("-p", dest="port", default=p._server_port, help="Port number [5030]")
    args = parser.parse_args()

    tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
    
    # Unsure of how to report different errors to Orca
    # Return values?  Seems ugly.

    try:
        pins, channels = tellie_server.read_pin_sequence()
        if pins is None:
            # Sequence is incomplete; handle in return type?
            sys.exit(1)
        else:
            # This is fine, report the pin in a print
            print pins
    except xmlrpclib.Fault, e:
        print "Error! attempting to exit safely", e
        tellie_server.stop()
    

    
