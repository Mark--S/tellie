#!/usr/bin/env python
#
# tellie_server
#
# Server to sit between tellie and ORCA, enabling 
# hardware interactions
#
# Author: Ed Leming
#         <e.leming@sussex.ac.uk>
#
# History:
# 2016/01/26: First instance
#
###########################################
###########################################

from SimpleXMLRPCServer import SimpleXMLRPCServer
from core import serial_command
import tellie_exception
import sys
import time
import argparse
# TONY'S LOG SERVER 
from snotdaq import logger

class ServiceRoot:
    pass

if __name__=="__main__":
    port = 5030
    # TODO: server should run with an argument (in case daq and tellie control are separate)
    server = SimpleXMLRPCServer(("localhost", port), allow_none=True)
    
    root = ServiceRoot()
    root.tellieCommands = serial_command.SerialCommand()

    server.register_instance(root, allow_dotted_names=True)

    print "serving..."
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "Exiting safely"
        safe_exit()
