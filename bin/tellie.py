#!/usr/bin/env python
#
# tellie.py
#
# Main control script to run Tellie.
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# History:
# 2013/03/08: First instance
#
###########################################
###########################################

import os
import sys
import argparse
import inspect
from SimpleXMLRPCServer import SimpleXMLRPCServer
from core import tellie_exception, serial_command
from common import tellie_logger
from common import parameters as p

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="debug", action="store_true", default=p._debug_mode, help="Debug mode")
    parser.add_argument("-p", dest="server_port", type=int, default=p._server_port, help="XMLRPC server port")
    parser.add_argument("-s", dest="serial_port", default=p._serial_port, help="Set TELLIE usb port")
    parser.add_argument("-t", dest="chip_type", default=p._chip_type, help="Select TELLIE chip type")
    parser.add_argument("-l", dest="logfile", default=p._logger_file, help="Log filename")
    args = parser.parse_args()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(args.debug)
    logger.set_log_file(args.logfile)

    # Dynamically load the correct class for the chip
    # Could do this with a factory style function
    try:
        command_class = getattr(serial_command, args.chip_type)
    except AttributeError:
        parser.print_help()
        print "Cannot find chip type, available include:"
        for name, obj in inspect.getmembers(sys.modules['core.serial_command']):
            if inspect.isclass(obj):
                print obj.__name__

    # Now try to open up the connection with the correct usb-serial port
    try:
        tellie_control = command_class(args.serial_port)
    except tellie_exception.TellieSerialException:
        print "Could not connect on serial port %s" % (args.serial_port)
        ports = []
        for p in os.listdir('/dev'):
            if p.startswith('ttyUSB'):          # Ubuntu
                ports.append(p)
            if p.startswith('tty.usbserial'):   # Mac
                ports.append(p)
            if p.startswith('ttyS'):            # Windows / CentOS  (?)
                ports.append(p)
        if len(ports) == 0:
            print "Could not find appropriate address! Is the TELLIE usb plugged in?"
        else:
            print "Candidates include:"
            for p in ports:
                print p
        raise

    # Begin an endless loop with safe exits in the case of errors / interrupts
    server = SimpleXMLRPCServer(("localhost", args.server_port), allow_none=True)
    server.register_instance(tellie_control)
    print "serving..."
    try:
        server.serve_forever()
    except KeyboardInterrupt, e:
        print "Exiting safely"
        tellie_control.stop()
    except tellie_exception.TellieException, e:
        print "Raised tellie exception, exiting safely"
        tellie_control.stop()
        raise
    except:
        print "Unknown exception! Try to safely exit"
        tellie_control.stop()
        raise
