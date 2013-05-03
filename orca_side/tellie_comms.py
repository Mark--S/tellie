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
        print 'Received', self.recv(1024)
        self.close()

def send_command(command):
    client = TellieComms(HOST,PORT,command)
    asyncore.loop()    

init_settings = {1:{'pulse_height':16383,
                     'pulse_width':0}}
init_command = 'I|'+json.dumps(init_settings)
fire_settings = {1:{'pulse_number':1000,
                    'pulse_delay':010.000}}
fire_command = 'F|'+json.dumps(fire_settings)
read_command = 'R'
exit_command = 'X'

init_out = send_command(init_command)
fire_out = send_command(fire_command)        
read_out = send_command(read_command)
exit_out = send_command(exit_command)
