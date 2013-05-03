#!/usr/bin/env python
#
# orca_comms
#
# TellieServer, TellieEcho
#
# TellieServer & TellieEcho: classes to handle
# requests from Orca and provide responses.
# Module also contains functions to parse and handle
# the communications from Orca.
#
# Author: Matt Mottram 
#         <m.mottram@sussex.ac.uk>
#
# History:
# 2013/03/13: First instance
#
###########################################
###########################################

import asyncore
import socket
import os
import json
import serial_command
import tellie_exception

### Inputs:
# Flags notify Tellie of the format of the input
# Should be separated by '|' from JSON settings where appropriate
_flagin_init = "I" # JSON of settings
_flagin_fire = "F" # Fire once, or multiple?
_flagin_stop = "X" # No settings
_flagin_read = "R" # No settings

### Responses:
# Flags notify Orca of the format of the output
# Should be separated by '|' from JSON responses where appropriate
_flagout_ready = "R" # list of channels prepared
_flagout_firing = "F" # no other information
_flagout_stopped = "X" # no other information
_flagout_pinout = "P" # SHOULD BE dict of channels and PIN readings
_flagout_notready = "Z" # response when polled for PIN, but firing incomplete
_flagout_error = "E" # no other information

def debug(debug_mode,message):
    if debug_mode==True:
        print "DEBUG::COMMS::"+message

class TellieServer(asyncore.dispatcher):
    """Server class for asynchronous I/O to Tellie"""
    def __init__(self,host,port,tellie_serial,debug_mode):
        """Create a socket, bind to it and listen"""
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.bind((host,port))
        self.listen(1)
        self._tellie_serial = tellie_serial
        self._debug_mode = debug_mode
    def handle_accept(self):
        """Handle connection requests"""
        debug(self._debug_mode,"handle accept")
        sock, address = self.accept()
        TellieEcho(sock,address,self._tellie_serial,self._debug_mode)

class TellieEcho(asyncore.dispatcher_with_send):
    """Echo handling class for Tellie responses"""
    def __init__(self,conn_sock,client_address,tellie_serial,debug_mode):
        """Initialisation function"""
        asyncore.dispatcher_with_send.__init__(self, conn_sock)
        self.client_address = client_address
        self._tellie_serial = tellie_serial
        self._debug_mode = debug_mode
    def handle_read(self):
        """Handle communication from Orca, echo accordingly"""
        debug(self._debug_mode,"handle read")
        self.out_buffer = self.recv(1024)
        debug(self._debug_mode,"read: %s"%(self.out_buffer))
        if not self.out_buffer:
            self.close()
        else:
            try:
                response = handle_request(self.out_buffer,self._tellie_serial)
                self.out_buffer = response
            except tellie_exception.TellieException,e:
                self.out_buffer=_flagout_error+"|"+str(e)
            
def handle_request(request,tellie_serial):
    """Handle the command from Orca"""
    response = None
    if len(request.split('|'))!=2:
        if request[0]==_flagin_stop:
            response = tellie_stop(tellie_serial)
        elif request[0] == _flagin_read:
            response = tellie_read(tellie_serial)
        else:
            response = _flagout_error
    else:
        bits = request.split('|')
        flagin = bits[0]
        settings = bits[1]
        #flagin,settings = request.split('|')[0]
        if flagin == _flagin_init:
            response = tellie_init(tellie_serial,settings)
        elif flagin == _flagin_fire:
            response = tellie_fire(tellie_serial,settings)
        else:
            response = _flagout_error
    return response
    
def tellie_stop(tellie_serial):
    """Send a request for tellie to stop firing"""
    buffer_contents = tellie_serial.stop()
    return _flagout_stopped+'|'+buffer_contents

def tellie_init(tellie_serial,json_settings):
    """Read a settings JSON, send commands to the tellie control box"""
    ### Required settings for initialisation:
    # Channel (LED) number(s)
    # ... Then for each LED:
    # Pulse height
    # Pulse width
    # Pulse number
    # Pulse delay
    # Channel delay
    settings = json.loads(json_settings)
    for led in settings:
        tellie_serial.select_channel(led)
        tellie_serial.set_pulse_height(settings[led]["pulse_height"])
        tellie_serial.set_pulse_width(settings[led]["pulse_width"])
    return _flagout_ready

def tellie_fire(tellie_serial,json_settings):
    """Fire Tellie according to the settings from Orca"""
    settings = json.loads(json_settings)
    n_led = len(settings)
    for led in settings:
        tellie_serial.select_channel(led)
        tellie_serial.set_pulse_number(settings[led]["pulse_number"])
        tellie_serial.set_pulse_delay(settings[led]["pulse_delay"])
    if n_led==1:
        tellie_serial.fire()
    else:
        led_list = []
        for led in settings:
            led_list.append(led)
        tellie_serial.select_channels(led_list)
        tellie_serial.fire()
    return _flagout_firing

def tellie_read(tellie_serial):
    """Read a the PINout from the fired channels"""
    try:
        pin_out = tellie_serial.read_pin()
        pin_flag = _flagout_pinout
        return "%s|%s" % (_flagout_pinout,pin_out)
    except tellie_exception.TellieException:
        pin_out = ""
        return _flagout_error
