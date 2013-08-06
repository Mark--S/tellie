#!/usr/bin/env python
#
# tellie_comms
#
# TellieComms
#
# Command functions to send to the Tellie
# listening server.  Receives responses and 
# handles them accordingly.
#
# Author: Matt Mottram 
#         <m.mottram@sussex.ac.uk>
#
# History:
# 2013/03/19: First instance
#
###########################################
###########################################

import os
import sys
import asyncore
import socket
import json
import time
import threading
from common import comms_flags, tellie_logger

HOST = '127.0.0.1'
PORT = 50050

class TellieComms(asyncore.dispatcher_with_send):
    def __init__(self, host, port, message):
        asyncore.dispatcher.__init__(self)
        self.logger = tellie_logger.TellieLogger.get_instance()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)        
        self.connect((host, port))
        self.out_buffer = message
        self._response = None
        self._error = None
        self.logger.debug("TellieComms::sending::"+self.out_buffer)

    def handle_close(self):
        self.close()

    def handle_read(self):
        self._response = self.recv(1024)
        self.logger.debug("TellieComms::received::"+self._response)
        self.close()

    def handle_error(self):        
        nil, t, v, tbinfo = asyncore.compact_traceback()
        if t == socket.error:
            self._error = "SOCKET ERROR"
        else:
            self._error = str(t)+" "+str(v)
        self.handle_close()

    def get_response(self):
        if self._response:
            if self._response.split('|')[0]==comms_flags.tellie_error:
                if len(self._response.split('|'))<2:
                    return True,'No error info'
                else:
                    return True,self._response.split('|')[1]
            else:
                return False,self._response
        elif self._error:
            return True,self._error
        else:
            return None,None

def send_command(command):
    client = TellieComms(HOST,PORT,command)
    asyncore.loop()        
    return client.get_response()

def send_init_command(settings):
    command = comms_flags.orca_init+"|"+json.dumps(settings)
    return send_command(command)

def send_fire_command(settings):
    command = comms_flags.orca_fire+"|"+json.dumps(settings)
    return send_command(command)

def send_read_command():
    command = comms_flags.orca_read
    return send_command(command)

def send_stop_command():
    command = comms_flags.orca_stop
    return send_command(command)

#init_settings = {1:{'pulse_height':16383,
#                     'pulse_width':0}}
#fire_settings = {1:{'pulse_number':100,
#                    'pulse_delay':010.000}}
#
#init_out = send_init_command(init_settings)
#fire_out = send_fire_command(fire_settings)
#read_out = send_read_command()
#exit_out = send_stop_command()
