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
from common import comms_flags, tellie_logger
import serial_command
import tellie_exception


class TellieServer(asyncore.dispatcher):
    """Server class for asynchronous I/O to Tellie"""
    def __init__(self,host,port,tellie_serial):
        """Create a socket, bind to it and listen"""
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.bind((host,port))
        self.listen(1)
        self._tellie_serial = tellie_serial
        self.logger = tellie_logger.TellieLogger.get_instance()
    def handle_accept(self):
        """Handle connection requests"""
        self.logger.debug("handle accept")
        sock, address = self.accept()
        TellieEcho(sock,address,self._tellie_serial)

class TellieEcho(asyncore.dispatcher_with_send):
    """Echo handling class for Tellie responses"""
    def __init__(self,conn_sock,client_address,tellie_serial):
        """Initialisation function"""
        asyncore.dispatcher_with_send.__init__(self, conn_sock)
        self.client_address = client_address
        self._tellie_serial = tellie_serial
        self.logger = tellie_logger.TellieLogger.get_instance()
    def handle_read(self):
        """Handle communication from Orca, echo accordingly"""
        self.logger.debug("handle read")
        self.out_buffer = self.recv(1024)
        self.logger.debug("read: %s"%(self.out_buffer))
        if not self.out_buffer:
            self.close()
        else:
            try:
                response = handle_request(self.out_buffer,self._tellie_serial)
                self.out_buffer = response
            except tellie_exception.TellieException,e:
                self.out_buffer=comms_flags.tellie_error+"|"+str(e)
            
def handle_request(request,tellie_serial):
    """Handle the command from Orca"""
    response = None
    if len(request.split('|'))!=2:
        if request[0]==comms_flags.orca_stop:
            response = tellie_stop(tellie_serial)
        elif request[0] == comms_flags.orca_read:
            response = tellie_read(tellie_serial)
        else:
            response = comms_flags.tellie_error+"|"+"Unknown input!"
    else:
        bits = request.split('|')
        flagin = bits[0]
        settings = bits[1]
        #flagin,settings = request.split('|')[0]
        if flagin == comms_flags.orca_init:
            response = tellie_init(tellie_serial,settings)
        elif flagin == comms_flags.orca_fire:
            response = tellie_fire(tellie_serial,settings)
        else:
            response = comms_flags.tellie_error+"|"+"Unknown input!"
    return response
    
def tellie_stop(tellie_serial):
    """Send a request for tellie to stop firing"""
    buffer_contents = tellie_serial.stop()
    return comms_flags.tellie_stopped+'|'+buffer_contents

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
        tellie_serial.set_fibre_delay(settings[led]["fibre_delay"])
    return comms_flags.tellie_ready

def tellie_fire(tellie_serial,json_settings):
    """Fire Tellie according to the settings from Orca"""
    settings = json.loads(json_settings)
    n_led = len(settings)
    tellie_serial.set_pulse_number(settings["pulse_number"])
    tellie_serial.set_pulse_delay(settings["pulse_delay"])
    tellie_serial.set_trigger_delay(settings["trigger_delay"])
    if n_led==1:
        tellie_serial.select_channel(settings.keys[0])
        tellie_serial.fire()
    else:
        led_list = []
        for led in settings:
            led_list.append(led)
        tellie_serial.select_channels(led_list)
        tellie_serial.fire()
    return comms_flags.tellie_firing

def tellie_read(tellie_serial):
    """Read a the PINout from the fired channels"""
    try:
        pin_out = tellie_serial.read_pin()
        if pin_out:
            return "%s|%s" % (comms_flags.tellie_pinout,pin_out)
        else:
            return comms_flags.tellie_notready
    except tellie_exception.TellieException,e:
        pin_out = ""
        print e,type(e)
        return comms_flags.tellie_error,"NOT YET..."
