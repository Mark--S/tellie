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
    (options, args) = parser.parse_args()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(options.debug)
    tellie_serial = serial_command.SerialCommand(options.port)
    try:
        run_tellie(tellie_serial)
    except KeyboardInterrupt:
        print 'quitting server'
        asyncore.ExitNow('Server is quitting')
        safe_exit(tellie_serial)
    except Exception,e:
        print "Quitting - not an interrupt"
        safe_exit(tellie_serial)
