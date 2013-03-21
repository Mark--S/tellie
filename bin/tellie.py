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
from core import tellie_exception, serial_command, orca_comms
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
    #try:
    tellie_serial = serial_command.SerialCommand()
    run_tellie(tellie_serial)
    #except:
    #    safe_exit(tellie_serial)
