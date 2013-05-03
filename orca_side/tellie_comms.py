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

HOST = '127.0.0.1'
PORT = 50050

class TellieComms(asyncore.dispatcher_with_send):
    def __init__(self, host, port, message):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.out_buffer = message

    def handle_close(self):
        self.close()

    def handle_read(self):
        self._response = self.recv(1024)
        print "Received:",self._response
        self.close()

    def get_response(self):
        if self._response:
            return self._response
        else:
            return None

_flagout_init = "I"
_flagout_fire = "F"
_flagout_read = "R"
_flagout_stop = "X"

def send_command(command):
    client = TellieComms(HOST,PORT,command)
    asyncore.loop()
    return client.get_response()

def send_init_command(settings):
    command = _flagout_init+"|"+json.dumps(settings)
    return send_command(command)

def send_fire_command(settings):
    command = _flagout_fire+"|"+json.dumps(settings)
    return send_command(command)

def send_read_command():
    command = _flagout_read
    return send_command(command)

def send_stop_command():
    command = _flagout_stop
    return send_command(command)

init_settings = {1:{'pulse_height':16383,
                     'pulse_width':0}}
fire_settings = {1:{'pulse_number':100,
                    'pulse_delay':010.000}}

init_out = send_init_command(init_settings)
fire_out = send_fire_command(fire_settings)
read_out = send_read_command()
exit_out = send_stop_command()
