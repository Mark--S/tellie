#!/usr/bin/env python
import argparse
import xmlrpclib
from common import parameters as p

if __name__=="__main__":
    parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
    parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
    parser.add_argument("-p", dest="port", default=p._server_port, help="Port number [5030]")
    args = parser.parse_args()

    tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))

    try:
        tellie_server.stop()
    except xmlrpclib.Fault:
        # Uh oh!
        raise
