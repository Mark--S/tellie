#!/usr/bin/env python
import argparse
import xmlrpclib
from snotdaq import logger
from common import parameters as p

if __name__=="__main__":
    try:
        parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default=p._server_port, help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
        _logger = logger.Logger("tellie", args.server, args.port)

        try:
            _logger.log(Logger.DEBUG, "Sending stop command to tellie server")
            tellie_server.stop()
        except xmlrpclib.Fault:
            _logger.log(Logger.WARNING, "Couldn't excecute tellie server stop command")
            # Uh oh!
            raise
    except:
        print "Unable to connect or send commands sucessfully to the Tellie hardware"
