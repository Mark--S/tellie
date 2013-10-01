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
from common import tellie_logger , parameters

_max_pulse_height = 16383
_max_pulse_width = 16383
_max_lo = 255.
_max_pulse_delay = 256.020
_min_pulse_delay = 0.1
_max_trigger_delay = 1275
_max_fibre_delay = 127.5
_max_pulse_number = 65025
_max_pulse_number_upper = 255
_max_pulse_number_lower = 255
_max_temp_probe = 64

_cmd_fire_continuous = "a"
_cmd_read_single_lower = "r"
_cmd_read_single_upper = "m"
_cmd_read_average_lower = "s"
_cmd_read_average_upper = "U"
_cmd_fire_series = "g"
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
_cmd_temp_select_lower =  "n"
_cmd_temp_read_lower = "T"
_cmd_temp_select_upper =  "f"
_cmd_temp_read_upper = "k"
_cmd_distable_trig_in = "B"

class SerialCommand(object):
    """Serial command object"""

    def __init__(self,port_name=None):
        """Initialise the serial command"""
        if port_name==None:
            self._port_name = "/dev/tty.usbserial-FTE3C0PG"        
        else:
            self._port_name = port_name
        self._port_timeout = 0.5        
        self._serial = serial.Serial(port=self._port_name, timeout=self._port_timeout)
        self.logger = tellie_logger.TellieLogger.get_instance()
        #cache current settings - remove need to re-command where possible
        #channel specific settings
        self._channel = [] #always a list
        self._current_pw = [-999]*96
        self._current_ph = [-999]*96
        self._current_fd = [-999]*96
        #global settings
        self._current_pn = None
        self._current_pd = None
        self._current_td = None
        #information on whether the channel is being fired
        self._firing = 0 #must wait for firing to complete
        self._reading = 0 #once a read command has been sent, dont send again!
        #temperature settings
        self._current_temp_probe = None
        #if a new channel is selected should force setting all new parameters
        #restriction only lifted once a fire command has been called
        self._force_setting = False 
            
    def __del__(self):
        """Deletion function"""
        self._serial.close()

    def _check_clear_buffer(self):
        """Many commands expect an empty buffer, fail if they are not!
        """
        buffer_read = self._serial.read(100)
        if buffer_read!="" and buffer_read!=None:
            raise tellie_exception.TellieException("Buffer not clear: %s"%(buffer_read))

    def _send_command(self,command,readout=True,buffer_check=None):
        """Send a command to the serial port.
        Command can be a chr/str (single write) or a list.
        Lists are used for e.g. a high/low bit command where
        the high bit could finish with an endline (i.e. endstream)"""
        self.logger.debug("_send_command")        
        if type(command) is str:
            command = [command]
        if type(command) is not list:
            raise tellie_exception.TellieException("Command is not a list: %s %s"%(command,type(command)))
        try:            
            for c in command:
                self._serial.write(c)       
        except:
            raise tellie_exception.TellieException("Lost connection with TELLIE control!")
        if buffer_check==None: # assume returns same as input
            buffer_check = ''
            for c in command:
                buffer_check += c
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
                    break
            if str(buffer_read)!=str(buffer_check):
                self.logger.debug("problem reading buffer, send %s, read %s"%(command,buffer_read))
                raise tellie_exception.TellieException("Unexpected buffer output:\nsaw: %s\nexpected: %s"%(buffer_read,buffer_check))
            else:
                self.logger.debug("success reading buffer")
        else:
            self.logger.debug("not a readout command")
                
    def _send_setting_command(self,command,buffer_check=None,while_fire=False):
        """Send non-firing command.  All of these should have a clear buffer before being used.
        Can set while_fire to True to allow a non-fire command to be sent while firing (will cause
        PIN readout to be flushed to buffer).
        """
        self.logger.debug("Send non-firing command")
        if self._firing==True:
            if while_fire==False:
                raise tellie_exception.TellieException("Cannot run command, in firing mode")
            else:
                #Assume that we CANNOT readout the buffer here!
                self._send_command(command=command,readout=False)
        else:
            self._check_clear_buffer()
            self._send_command(command=command,buffer_check=buffer_check)

    def _send_global_setting_command(self,command,buffer_check=None,while_fire=False):
        """Send non-firing command that affects all channels.
        Can set while_fire to True to allow a non-fire command to be sent while firing (will cause
        PIN readout to be flushed to buffer).
        """
        self.logger.debug("Send global setting command %s"%(command))
        self._send_setting_command(command=command,buffer_check=buffer_check,while_fire=while_fire)

    def _send_channel_setting_command(self,command,buffer_check=None,while_fire=False):
        """Send non-firing command for specific channel.
        Can set while_fire to True to allow a non-fire command to be sent while firing (will cause
        PIN readout to be flushed to buffer).
        """
        self.logger.debug("Send channel setting command %s"%(command))
        if self._channel==None or self._channel==[]:
            raise tellie_exception.TellieException("Cannot run channel command, no channel selected")
        if len(self._channel)!=1:
            raise tellie_exception.TellieException("Cannot run channel command, must have single channel selected: %s"%(self._channel))
        self._send_setting_command(command=command,buffer_check=buffer_check,while_fire=while_fire)

    def fire(self,while_fire=False):
        """Fire tellie, place class into firing mode.
        Can send a fire command while already in fire mode if required."""
        self.logger.debug("Fire!")
        if self._firing==True and while_fire==False:
            raise tellie_exception.TellieException("Cannot fire, already in firing mode")
        self.check_ready()
        # Set readout to false when firing (must read
        # averaged pin at some later time).
        cmd = None
        buffer_check = _cmd_fire_series+"K"
        self._send_command(_cmd_fire_series,buffer_check=buffer_check)
        #if self._channel <= 56: #up to box 7
        #    cmd = _cmd_fire_series_lower
        #else:
        #    cmd = _cmd_fire_series_upper
        #self._send_command(cmd,False)
        self._firing = True
        self._force_setting = False

    def fire_single(self):
        """Fire single pulse
        """
        if self._firing==True:
            raise tellie_exception.TellieException("Cannot fire, already in firing mode")
        if self._channel <= 56: #up to box 7
            cmd = _cmd_fire_single_lower
        else:
            cmd = _cmd_fire_single_upper
        self._send_command(cmd,False)
        self._firing = True
        pin = self.read_pin(self._channel[0])
        while pin==None:
            pin = self.read_pin(self._channel[0])
        return pin
        
    def fire_continuous(self):
        """Fire Tellie in continous mode.
        """
        if self._firing==True:
            raise tellie_exception.TellieException("Cannot fire, already in firing mode")
        self._send_command(_cmd_fire_continuous,False)
        self._firing = True
        self._force_setting = False

    def read_buffer(self,n=100):
        return self._serial.read(n)

    def stop(self):
        """Stop firing tellie"""
        self.logger.debug("Stop firing!")
        self._send_command(_cmd_stop,False)        
        buffer_contents = self._serial.read(100)
        self._firing = False
        return buffer_contents

    def read_pin(self,channel=None,timeout=2.0,final=True):
        """Read the pin diode output, should always follow a fire command,
        Provide channel number to select specific channel, otherwise, receive dict of all channels"""
        self.logger.debug("Read PINOUT")
        if self._firing!=True:
            raise tellie_exception.TellieException("Cannot read pin, not in firing mode")
        if channel!=None:
            if self._reading==True:
                if channel!=self._channel[0]:
                    raise tellie_exception.TellieException("Cannot read pin for channel %s, already trying to read channel %s"%(channel,self._channel[0]))
            else:
                self.select_channel(channel)      
            if self._channel[0] <= 56: #up to box 7
                cmd = _cmd_read_average_lower
            else:
                cmd = _cmd_read_average_upper
            if not self._reading:
                self._send_command(cmd,False)
            pattern = re.compile(r"""\d+""")
            start = time.time()
            pin = []
            while (time.time()-start)<timeout:
                output = self._serial.read(100)
                pin = pattern.findall(output)
                if len(pin):
                    break
                time.sleep(0.1)
            if len(pin)>1:
                self._firing = False
                self._reading = False
                raise tellie_exception.TellieException("Bad number of PIN readouts: %s %s"%(len(pin),pin))
            elif len(pin)==0:
                self._reading = True
                return None            
            self._reading = False
            if final==True:
                self._firing = False
            return pin[0]
        else:
            #check all PINs from the last firing sequence
            #need to store a copy of which pins were read
            channel_list = self._channel
            channel_dict = {}
            final_read = False
            for i,channel in enumerate(channel_list):
                if i==len(channel_list)-1:
                    final_read = True
                pin = self.read_pin(channel,final=final_read)
                channel_dict[channel] = pin
            return channel_dict,channel_list

    def check_ready(self):
        """Check that all settings have been set"""
        not_set = []
        for channel in self._channel:
            if self._current_pw[channel-1]==None:
                not_set += ["Pulse width"]
            if self._current_ph[channel-1]==None:
                not_set += ["Pulse height"]
            if self._current_fd[channel-1]==None:
                not_set += ["Fibre delay"]
        if self._current_pn==None:
            not_set += ["Pulse number"]
        if self._current_pd==None:
            not_set += ["Pulse delay"]
        if self._current_td==None:
            not_set += ["Trigger delay"]
        print not_set
        if not_set!=[]:
            raise tellie_exception.TellieException("Undefined options: %s"%(", ".join(opt for opt in not_set)))

    def clear_channel(self):
        """Unselect the channel"""
        self.logger.debug("Clear channel")
        self._send_command(_cmd_channel_clear)
        self._channel = []

    def clear_channel_settings(self,channel):
        """Clear settings for a specific channel"""
        self._current_pw[channel-1] = None
        self._current_ph[channel-1] = None
        self._current_fd[channel-1] = None

    def clear_global_settings(self):
        """Clear settings that affect all channels"""
        self._current_pn = None
        self._current_pd = None
        self._current_td = None

    def select_channel(self,channel):
        """Select a channel"""
        if type(channel) is not int:
            channel = int(channel)
        if self._channel!=[]:
            if self._channel==[channel]:
                #channel already selected
                return 
        self.logger.debug("Select channel %s %s"%(channel,type(channel)))
        command = _cmd_channel_select_single_start+chr(channel)+_cmd_channel_select_single_end
        buffer_check = "B"+str((int(channel)-1)/8+1)+_cmd_channel_select_single_end
        self._send_command(command=command,buffer_check=buffer_check)
        self._channel = [channel]

    def select_channels(self,channels):
        """Select multiple channels, expects list for channels"""
        self.logger.debug("Select channels %s %s"%(channels,type(channels)))
        self.clear_channel()
        command = _cmd_channel_select_many_start
        for channel in channels:
            print channel
            command += chr(channel)
        command += _cmd_channel_select_many_end
        buffer_check = "B"+str((int(channels[0])-1)/8+1)+_cmd_channel_select_many_end
        print "SEND CHANNELS","CMD",command,"BUF",buffer_check
        self._send_command(command=command,buffer_check=buffer_check)
        print "DONE!"
        self._channel = channels

    def set_pulse_height(self,par):
        """Set the pulse height for the selected channel"""
        if len(self._channel)!=1:
            raise tellie_exception.TellieException("Cannot set parameter with channels set as %s"%(self._channel))
        if par==self._current_ph[self._channel[0]] and not self._force_setting:
            pass #same as current setting
        else:
            self.logger.debug("Set pulse height %s %s"%(par,type(par)))        
            command,buffer_check = command_pulse_height(par)
            self._send_channel_setting_command(command=command,buffer_check=buffer_check)
            self._current_ph[self._channel[0]] = par

    def set_pulse_width(self,par,while_fire=False):
        """Set the pulse width for the selected channel.
        This is the only setting that can be modified while in firing mode."""
        if len(self._channel)!=1:
            raise tellie_exception.TellieException("Cannot set parameter with channels set as %s"%(self._channel))
        if par==self._current_pw[self._channel[0]] and not self._force_setting:
            pass #same as current setting
        else:
            self.logger.debug("Set pulse width %s %s"%(par,type(par)))
            command,buffer_check = command_pulse_width(par)
            if while_fire and self._firing:
                self._send_channel_setting_command(command=command,while_fire=while_fire)
            else:
                self._send_channel_setting_command(command=command,buffer_check=buffer_check)
            self._current_pw[self._channel[0]] = par

    def set_fibre_delay(self,par):
        """Set the fibre (channel) delay for the selected channel"""
        if len(self._channel)!=1:
            raise tellie_exception.TellieException("Cannot set parameter with channels set as %s"%(self._channel))
        if par==self._current_fd[self._channel[0]] and not self._force_setting:
            pass
        else:
            self.logger.debug("Set Fibre delay %s %s"%(par,type(par)))
            command,buffer_check = command_fibre_delay(par)
            self._send_channel_setting_command(command=command,buffer_check=buffer_check)
            self._current_fd[self._channel[0]] = par

    def set_pulse_number(self,par):
        """Set the number of pulses to fire (global setting)"""
        if par==self._current_pn and not self._force_setting:
            pass
        else:
            self.logger.debug("Set pulse number %s %s"%(par,type(par)))
            command,buffer_check = command_pulse_number(par)
            self._send_global_setting_command(command=command,buffer_check=buffer_check)
            self._current_pn = par

    def set_pulse_delay(self,par):
        """Set the delay between pulses (global setting)"""
        if par==self._current_pd and not self._force_setting:
            pass
        else:
            self.logger.debug("Set pulse delay %s %s"%(par,type(par)))
            command,buffer_check = command_pulse_delay(par)
            self._send_global_setting_command(command=command,buffer_check=buffer_check)
            self._current_pd = par

    def set_trigger_delay(self,par):
        """Set the trigger delay (global setting)"""
        if par==self._current_td and not self._force_setting:
            pass
        else:
            self.logger.debug("Set trigger delay %s %s"%(par,type(par)))
            command,buffer_check = command_trigger_delay(par)
            self._send_global_setting_command(command=command,buffer_check=buffer_check)
            self._current_td = par

    def select_temp_probe(self,par):
        """Select the temperature probe to read"""
        if par==self._current_temp_probe and not self._force_setting:
            pass
        else:
            self.logger.debug("Select temperature probe %s %s"%(par,type(par)))
            command,buffer_check = command_select_temp(par)
            self._send_command(command=command,readout=False)
            self._current_temp_probe = par
            #read the temperature twice
            #first reading is always junk
            #second reading is sometimes junk
            self.read_temp()
            self.read_temp()
            
    def read_temp(self,timeout=1.0):
        """Read the temperature"""
        if self._current_temp_probe==None:
            raise tellie_exception.TellieException("Cannot read temp: no probe selected")
        cmd = ""
        if self._current_temp_probe < 33 and self._current_temp_probe > 0:
            cmd = _cmd_temp_read_lower
        elif self._current_temp_probe < _max_temp_probe+1:
            cmd = _cmd_temp_read_upper
        else:
            raise tellie_exception.TellieException("Temp probe not in known range")            
        self._send_command(command=cmd,readout=False)
        pattern = re.compile(r"""[-+]?\d*\.\d+|\d+""")
        #wait for a few seconds before reading out
        temp = None
        start = time.time()
        while temp==None:
            output = self._serial.read(100)
            self.logger.debug("Buffer: %s"%output)
            temp = pattern.findall(output)
            if time.time() - start > timeout:
                raise tellie_exception.TellieException("Temperature read timeout!")
        if len(temp)>1:
            raise tellie_exception.TellieException("Bad number of temp readouts: %s %s"%(len(temp),temp))
        temp = float(temp[0])
        return temp

    def disable_external_trigger(self):
        """Disable the external trigger"""
        self._send_command(command="B")

##################################################
# Command options and corresponding buffer outputs
#

def command_pulse_height(par):
    """Get the command to set a pulse height"""  
    if par>_max_pulse_height or par<0:
        raise tellie_exception.TellieException("Invalid pulse height: %s"%par)
    hi = par >> 8
    lo = par & 255
    command = [_cmd_ph_hi+chr(hi)]
    command+= [_cmd_ph_lo+chr(lo)]
    command+= [_cmd_ph_end]
    buffer_check = _cmd_ph_hi+_cmd_ph_lo+_cmd_ph_end  
    return command,buffer_check

def command_pulse_width(par):
    """Get the command to set a pulse width"""
    if par>_max_pulse_width or par<0:
        raise tellie_exception.TellieException("Invalid pulse width: %s %s %s"%(par,_max_pulse_width,par>_max_pulse_width))
    hi = par >> 8
    lo = par & 255
    command = [_cmd_pw_hi+chr(hi)]
    command+= [_cmd_pw_lo+chr(lo)+_cmd_pw_end]
    buffer_check = _cmd_pw_hi+_cmd_pw_lo+_cmd_pw_end
    return command,buffer_check

def command_pulse_number(par):
    """Get the command to set a pulse number"""
    if par>_max_pulse_number or par<0:
        raise tellie_exception.TellieException("Invalid pulse number: %s"%(par))
    par = int(par)
    adjusted, actual_par, hi, lo = parameters.pulse_number(par)
    if adjusted == True:
        raise tellie_exception.TellieException("Invalid pulse number: %s"%(par))
    command = [_cmd_pn_hi+chr(hi)]
    command+= [_cmd_pn_lo+chr(lo)]
    buffer_check = _cmd_pn_hi + _cmd_pn_lo
    return command,buffer_check
    
def command_pulse_delay(par):
    """Get the command to set a pulse delay"""
    if par>_max_pulse_delay or par<0:
        raise tellie_exception.TellieException("Invalid pulse delay: %s"%par)
    ms = int(par)
    us = int((par-ms)*250)
    command = [_cmd_pd+chr(ms)]
    command+= [chr(us)]
    buffer_check = _cmd_pd
    return command,buffer_check
    
def command_trigger_delay(par):
    """Get the command to set a trigger delay"""
    if par>_max_trigger_delay or par<0:
        raise tellie_exception.TellieException("Invalid trigger delay: %s"%par)
    command = [_cmd_td+chr(par/5)]
    buffer_check = _cmd_td
    return command,buffer_check
    
def command_fibre_delay(par):
    """Get the command to set a fibre delay"""
    if par>_max_fibre_delay or par<0:
        raise tellie_exception.TellieException("Invalid fibre delay: %s"%par)
    adjusted,adj_delay,setting = parameters.fibre_delay(par)
    print "COMMAND",par,adjusted,adj_delay,setting
    if adjusted==True:
        raise tellie_exception.TellieException("Invalid delay: %s"%(par))
    command = [_cmd_fd+chr(setting)]
    buffer_check = _cmd_fd
    return command,buffer_check
    
def command_select_temp(par):
    """Select a temperature probe to read"""
    if par>_max_temp_probe or par<0:
        raise tellie_exception.TellieException("Invalid temp. probe number: %s"%par)    
    cmd = ""
    par = par
    if par < 33 and par > 0:
        cmd = _cmd_temp_select_lower
        par = par
    elif par < _max_temp_probe+1:
        cmd = _cmd_temp_select_upper
        par = par - 32 #lower
    else:
        raise tellie_exception.TellieException("Invalid temp. probe number: %s"%par)  
    command = [cmd+chr(par)]
    return command,None # nothing in buffer
