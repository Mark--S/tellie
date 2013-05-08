#!/usr/bin/env python
#
# serial_command
#
# SerialCommand
#
# Command functions to send to the Tellie
# control box
#
# Author: Matt Mottram 
#         <m.mottram@sussex.ac.uk>
#
# History:
# 2013/03/08: First instance
#
###########################################
###########################################

import serial
import tellie_exception
import re
import sys
import time

_max_pulse_height = 16383
_max_pulse_width = 16363
_max_lo = 255.
_max_pulse_delay = 256.020
_min_pulse_delay = 0.1
_max_trigger_delay = 1275
_max_fibre_delay = 127.5
_max_pulse_number = 62025

_cmd_fire_series = "s"
_cmd_stop = "X"
_cmd_channel_clear = "C"
_cmd_channel_select_single_start = "I"
_cmd_channel_select_single_end = "N"
_cmd_channel_select_many_start = "J"
_cmd_channel_select_many_end = "E"
_cmd_ph_hi = "L"
_cmd_ph_lo = "M"
_cmd_ph_end = "P"
_cmd_pw_hi = "Q"
_cmd_pw_lo = "R"
_cmd_pw_end = "S"
_cmd_pn_hi = "H"
_cmd_pn_lo = "G"
_cmd_pd = "u"
_cmd_td = "d"
_cmd_fd = "e"

class SerialCommand(object):
    """Serial command object"""

    def __init__(self,debug_mode=False):
        """Initialise the serial command"""
        self._port_name = "/dev/tty.usbserial-FTE3C0PG"
        self._port_timeout = 0.5
        self._firing = False
        self._channel = None
        self._debug_mode = debug_mode
        self._serial = serial.Serial(port=self._port_name, timeout=self._port_timeout)
            
    def __del__(self):
        """Deletion function"""
        self._serial.close()

    def _debug(self,message):
        """Print message
        """
        if self._debug_mode:
            print "DEBUG::"+message

    def _check_clear_buffer(self):
        """Many commands expect an empty buffer, fail if they are not!
        """
        buffer_read = self._serial.read(100)
        if buffer_read!="" and buffer_read!=None:
            raise tellie_exception.TellieException("Buffer not clear: %s"%(buffer_read))

    def _send_command(self,command,readout=True,buffer_check=None):
        """Send a command to the serial port."""
        self._debug("_send_command")
        try:
            self._serial.write(command)        
        except:
            raise tellie_exception.TellieException("Lost connection with TELLIE control!")
        if buffer_check==None: # assume returns same as input
            buffer_check = command
        if readout==True:
            # Usually need to empty the buffer.
            # Use arbitrary large number of chars.
            buffer_read = ""
            #print 'in:',command,'want:',buffer_check,'out:',buffer_read
            n_read = 0
            while str(buffer_read)!=str(buffer_check):
                buffer_read += self._serial.read(100)
                time.sleep(0.01)
                #print 'LOOPING! in:'+command+':want:'+buffer_check+':out:'+buffer_read+':'
                n_read+=1
                if n_read>10:
                    raise tellie_exception.TellieException("Unexpected buffer output: %s"%(buffer_read))
        else:
            pass
                
    def _send_setting_command(self,command,buffer_check=None):
        """Send non-firing command.  All of these should have a clear buffer before being used."""
        self._debug("Send non-firing command")
        if self._firing==True:
            raise tellie_exception.TellieException("Cannot run command, in firing mode")
        self._check_clear_buffer()
        self._send_command(command=command,buffer_check=buffer_check)
            
    def _send_channel_setting_command(self,command,buffer_check=None):
        """Send non-firing command for specific channel"""
        self._debug("Send channel setting command %s"%(command))
        if self._channel==None:
            raise tellie_exception.TellieException("Cannot run channel command, no channel selected")
        if len(self._channel)!=1:
            raise tellie_exception.TellieException("Cannot run channel command, too many channels selected")
        self._send_setting_command(command=command,buffer_check=buffer_check)

    def fire(self):
        """Fire tellie, place class into firing mode"""
        self._debug("Fire!")
        if self._firing==True:
            raise tellie_exception.TellieException("Cannot fire, already in firing mode")
        # Set readout to false when firing (must read
        # averaged pin at some later time).
        self._send_command(_cmd_fire_series,False)
        self._firing = True

    def stop(self):
        """Stop firing tellie"""
        self._debug("Stop firing!")
        self._send_command(_cmd_stop,False)        
        buffer_contents = self._serial.read(100)
        self._firing = False
        return buffer_contents

    def read_pin(self,channel=None):
        """Read the pin diode output, should always follow a fire command"""
        self._debug("Read PINOUT")
        if self._firing!=True:
            raise tellie_exception.TellieException("Cannot read pin, not in firing mode")
        ## must re-select the LED!
        #if channel==None:
        #    channel = self._channel[0]
        #command = _cmd_channel_select_single_start+chr(channel)+_cmd_channel_select_single_end
        #buffer_check = "B"+str((int(channel)+1)/8 + 1)+_cmd_channel_select_single_end
        #self._send_command(command=command,buffer_check=buffer_check)
        pattern = re.compile(r"""\d+""")
        output = self._serial.read(100)        
        pin = pattern.findall(output)
        if len(pin)>1:
            raise tellie_exception.TellieException("Bad number of PIN readouts: %s"%(len(pin)))
        elif len(pin)==0:
            return None
        self._firing = False
        return pin[0]

    def clear_channel(self):
        """Unselect the channel"""
        self._debug("Clear channel")
        self._send_setting_command(_cmd_channel_clear)
        self._channel = None

    def select_channel(self,channel):
        """Select a channel"""
        self._debug("Select channel %s %s"%(channel,type(channel)))
        if self._channel!=None:
            self.clear_channel()
        if type(channel) is not int:
            channel = int(channel)
        command = _cmd_channel_select_single_start+chr(channel)+_cmd_channel_select_single_end
        buffer_check = "B"+str((int(channel)+1)/8 + 1)+_cmd_channel_select_single_end
        self._send_setting_command(command=command,buffer_check=buffer_check)
        self._channel = [channel]

    def select_channels(self,channels):
        """Select multiple channels, expects list for channels"""
        self._debug("Select channels %s %s"%(channels,type(channels)))
        self.clear_channel()
        command = ""
        for channel in channels:
            command += _cmd_channel_select_many_start+chr(channel)
        command += _cmd_channel_select_many_end
        self._send_setting_command(command=command,buffer_check=buffer_check)

    def set_pulse_height(self,par):
        """Set the pulse height for the selected channel"""
        self._debug("Set pulse height %s %s"%(par,type(par)))
        command,buffer_check = command_pulse_height(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

    def set_pulse_width(self,par):
        """Set the pulse width for the selected channel"""
        self._debug("Set pulse width %s %s"%(par,type(par)))
        command,buffer_check = command_pulse_width(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

    def set_pulse_number(self,par):
        """Set the number of pulses for the selected channel"""
        self._debug("Set pulse number %s %s"%(par,type(par)))
        command,buffer_check = command_pulse_number(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

    def set_pulse_delay(self,par):
        """Set the delay between pulses for the selected channel"""
        self._debug("Set pulse delay %s %s"%(par,type(par)))
        command,buffer_check = command_pulse_delay(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

    def set_trigger_delay(self,par):
        """Set the trigger delay for the selected channel"""
        self._debug("Set trigger delay %s %s"%(par,type(par)))
        command,buffer_check = command_trigger_delay(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

    def set_fibre_delay(self,par):
        """Set the fibre (channel) delay for the selected channel"""
        self._debug("Set Fibre delay %s %s"%(par,type(par)))
        command,buffer_check = command_fibre_delay(par)
        self._send_channel_setting_command(command=command,buffer_check=buffer_check)

##################################################
# Command options and corresponding buffer outputs
#

def command_pulse_height(par):
    """Get the command to set a pulse height"""  
    if par>_max_pulse_height or par<0:
        raise tellie_exception.TellieException("Invalid pulse height: %s"%par)
    hi = par >> 8
    lo = par & 255
    command = _cmd_ph_hi+chr(hi)+_cmd_ph_lo+chr(lo)+_cmd_ph_end
    buffer_check = _cmd_ph_hi+_cmd_ph_lo+_cmd_ph_end  
    return command,buffer_check

def command_pulse_width(par):
    """Get the command to set a pulse width"""
    if par>_max_pulse_width or par<0:
        raise tellie_exception.TellieException("Invalid pulse width: %s"%par)
    hi = par >> 8
    lo = par & 255
    command = _cmd_pw_hi+chr(hi)+_cmd_pw_lo+chr(lo)+_cmd_pw_end
    buffer_check = _cmd_pw_hi+_cmd_pw_lo+_cmd_pw_end
    return command,buffer_check

def command_pulse_number(par):
    """Get the command to set a pulse number"""
    if par>_max_pulse_number or par<0:
        raise tellie_exception.TellieException("Invalid pulse number: %s"%par)
    hi = int(par/255.)
    lo = int((par/255. - hi)*255)
    command = _cmd_pn_hi+chr(hi)+_cmd_pn_lo+chr(lo)
    buffer_check = _cmd_pn_hi + _cmd_pn_lo
    return command,buffer_check
    
def command_pulse_delay(par):
    """Get the command to set a pulse delay"""
    if par>_max_pulse_delay or par<0:
        raise tellie_exception.TellieException("Invalid pulse delay: %s"%par)
    ms = int(par)
    us = int((par-ms)*250)
    command = _cmd_pd+chr(ms)+chr(us)
    buffer_check = _cmd_pd
    return command,buffer_check
    
def command_trigger_delay(par):
    """Get the command to set a trigger delay"""
    if par>_max_trigger_delay or par<0:
        raise tellie_exception.TellieException("Invalid trigger delay: %s"%par)
    command = _cmd_td+chr(par/5)
    buffer_check = _cmd_td
    return command,buffer_check
    
def command_fibre_delay(par):
    """Get the command to set a fibre delay"""
    if par>_max_fibre_delay or par<0:
        raise tellie_exception.TellieException("Invalid fibre delay: %s"%fd)
    command = _cmd_fd+chr(par)
    buffer_check = _cmd_fd
    return command,buffer_check
    
