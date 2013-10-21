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
import optparse
import inspect
from core import tellie_exception, serial_command, orca_comms
from common import tellie_logger
import asyncore

def safe_exit(tellie_serial):
    """Stop any firing before exiting"""
    print 'Exiting safely!'
    tellie_serial.stop()

def run_tellie(tellie_serial):
    """Main operation loop for tellie control"""
    server = orca_comms.TellieServer('',50050,tellie_serial)
    asyncore.loop()

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d",dest="debug",action="store_true",default=False,help="Debug mode")
    parser.add_option("-p",dest="port",default=None,help="set non-default tellie address")
    parser.add_option("-t",dest="chip_type",default="SNO6C",help="Select TELLIE chip type")
    (options, args) = parser.parse_args()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(options.debug)
    try:
        command_object = getattr(serial_command, options.chip_type)
    except AttributeError:
        parser.print_help()
        print "Cannot find chip type, available include:"
        for name, obj in inspect.getmembers(sys.modules['core.serial_command']):
            if inspect.isclass(obj):
                print obj.__name__
    try:
        tellie_serial = command_object(options.port)
    except tellie_exception.TellieSerialException:
        print "Could not connect on port %s" % (options.port)
        ports = []
        for p in os.listdir('/dev'):
            if p.startswith('tty.usbserial'):
                ports.append(p)
        if len(ports)==0:
            print "Could not find appropriate address! Is the TELLIE usb plugged in?"
        else:
            print "Candidates include:"
            for p in ports:
                print p
        sys.exit(1)
    try:
        run_tellie(tellie_serial)
    except KeyboardInterrupt:
        print 'quitting server'
        asyncore.ExitNow('Server is quitting')
        safe_exit(tellie_serial)
    except Exception,e:
        print "Quitting - not an interrupt"
        safe_exit(tellie_serial)
