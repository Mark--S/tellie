#!/usr/bin/env python
import argparse
import xmlrpclib

if __name__=="__main__":
    try:
        print "Attemping to the tellie software"
        parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default="5030", help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))

        try:
            tellie_server.stop()
        except xmlrpclib.Fault:
            # Uh oh!
            raise
    except:
        print "Unable to connect or send commands sucessfully to the Tellie hardware"
