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
# 2013/10/21: Added new classes for different chips, pep8
#
###########################################
###########################################

from SimpleXMLRPCServer import SimpleXMLRPCServer
import serial
import tellie_exception
import re
import sys
import time
from common import tellie_logger, parameters
from snotdaq import Logger
import argparse
# TONY's LOG SERVER 
from snotdaq import logger

port = 5030
# TODO: server should run with an argument (in case daq and tellie control are separate)
server = SimpleXMLRPCServer(("localhost", port), allow_none=True)

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
_cmd_fire_average_lower = "s"
_cmd_fire_average_upper = "U"
_cmd_fire_series = "g"
_buffer_end_sequence = "K"
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
_cmd_temp_select_lower = "n"
_cmd_temp_read_lower = "T"
_cmd_temp_select_upper = "f"
_cmd_temp_read_upper = "k"
_cmd_distable_trig_in = "B"

_serial = None
_logger = None
_firing = False
_reading = False
_channel = []
_current_pw = [-999]*96
_current_ph = [-999]*96
_current_fd = [-999]*96
_current_pn = None
_current_pd = None
_current_td = None
_current_temp_probe = None
_force_setting = False


def initialise_tellie(port_name=None):
    """Initialise the serial command"""
    global _serial, _logger, _firing, _reading, _channel
    if not port_name:
        port_name = "/dev/tty.usbserial-FTE3C0PG"
    port_timeout = 0.3
    _serial = None
    try:
        _serial = serial.Serial(port=port_name, timeout=port_timeout)
        _logger.log(logger.DEBUG, "Serial connection open: %s" % _serial)
    except serial.SerialException, e:
        raise tellie_exception.TellieSerialException(e)
    #information on whether the channel is being fired
    _logger = logger.Logger("tellie", "localhost", port)
    _firing = False
    _reading = False
    _channel = []
    reset()
    #send a clear channel command, just in case
    clear_channel()

def safe_exit():
    """Deletion function"""
    stop()
    _serial.close()

def _check_clear_buffer():
    """Many commands expect an empty buffer, fail if they are not!
    """
    buffer_read = _serial.read(100)
    if buffer_read != "":
        raise tellie_exception.TellieException("Buffer not clear: %s" % (buffer_read))

def _send_command(command, readout=True, buffer_check=None):
    """Send a command to the serial port.
    Command can be a chr/str (single write) or a list.
    Lists are used for e.g. a high/low bit command where
    the high bit could finish with an endline (i.e. endstream)"""
    _logger.log(logger.DEBUG, "_send_command:%s" % command)
    if type(command) is str:
        command = [command]
    if type(command) is not list:
        raise tellie_exception.TellieException("Command is not a list: %s %s" % (command, type(command)))
    try:
        for c in command:
            _serial.write(c)
    except:
        raise tellie_exception.TellieException("Lost connection with TELLIE control!")
    if not buffer_check: # assume returns same as input
        buffer_check = ''
        for c in command:
            buffer_check += c
    if readout is True:
        # One read command (with default timeout of 0.1s) should be
        # enough to get all the chars from the readout.
        buffer_read = _serial.read(len(buffer_check))
        if str(buffer_read)!=str(buffer_check):
            _logger.log(logger.DEBUG, "problem reading buffer, send %s, read %s" % (command, buffer_read))
            #clear anything else that might be in there
            time.sleep(0.1)
            remainder = _serial.read(100)
            _serial.write("X") # send a stop
            time.sleep(0.1)
            _serial.write("C") # send a clear
            time.sleep(0.1)
            _serial.read(100)
            message = "Unexpected buffer output:\nsaw: %s, remainder %s\nexpected: %s" % (buffer_read, remainder, buffer_check)
            _logger.warn(message)
            raise tellie_exception.TellieException(message)
        else:
            _logger.log(logger.DEBUG, "success reading buffer:%s" % buffer_read)
    else:
        _logger.log(logger.DEBUG, "not a readout command")

def _send_setting_command(command, buffer_check=None, while_fire=False):
    """Send non-firing command.
    All of these should have a clear buffer before being used.  Can set
    while_fire to True to allow a non-fire command to be sent while firing
    (will cause PIN readout to be flushed to buffer).
    """
    _logger.log(logger.DEBUG, "Send non-firing command")
    if _firing is True:
        if while_fire is False:
            raise tellie_exception.TellieException("Cannot run command, in firing mode")
        else:
            #Assume that we CANNOT readout the buffer here!
            _send_command(command=command, readout=False)
    else:
        _check_clear_buffer()
        _send_command(command=command, buffer_check=buffer_check)

def _send_global_setting_command(command, buffer_check=None, while_fire=False):
    """Send non-firing command that affects all channels.
    Can set while_fire to True to allow a non-fire command to be sent
    while firing (will cause PIN readout to be flushed to buffer).
    """
    _logger.log(logger.DEBUG, "Send global setting command %s" % (command))
    _send_setting_command(command=command, buffer_check=buffer_check, while_fire=while_fire)

def _send_channel_setting_command(command, buffer_check=None, while_fire=False):
    """Send non-firing command for specific channel.
    Can set while_fire to True to allow a non-fire command to be sent while
    firing (will cause PIN readout to be flushed to buffer).
    """
    _logger.log(logger.DEBUG, "Send channel setting command %s" % (command))
    if not _channel or _channel == []:
        raise tellie_exception.TellieException("Cannot run channel command, no channel selected")
    if len(_channel)!=1:
        raise tellie_exception.TellieException("Cannot run channel command, must have single channel selected: %s" % (_channel))
    _send_setting_command(command=command, buffer_check=buffer_check, while_fire=while_fire)

def reset():
    """Send a reset command!

    Assumes that the port is open (which it is by default)
    """
    _logger.log(logger.DEBUG, "Reset!")
    _serial.setRTS(True)
    # sleep, just in case
    time.sleep(3.0)
    _serial.setRTS(False)
    # close the port and reopen?
    time.sleep(3.0)

def fire(while_fire=False):
    """Fire tellie, place class into firing mode.
    Can send a fire command while already in fire mode if required."""
    global _firing, _force_setting
    _logger.log(logger.DEBUG, "Fire!")
    if _firing is True and while_fire is False:
        raise tellie_exception.TellieException("Cannot fire, already in firing mode")
    check_ready()
    # Set readout to false when firing (must read
    # averaged pin at some later time).
    cmd = None
    buffer_check = _cmd_fire_series
    #if the series is less than 0.5 seconds, also check for the end of sequence
    if (_current_pn * _current_pd) < 500:
        buffer_check += _buffer_end_sequence
        _send_command(_cmd_fire_series, buffer_check=buffer_check)
    else:
        _send_command(_cmd_fire_series, buffer_check=buffer_check)
        _firing = True #still firing
    _force_setting = False

def fire_sequence(while_fire=False):
    """Fire in sequence mode, can only be done for a single channel.
    """
    global _firing, _force_setting
    _logger.log(logger.DEBUG, "Fire sequence!")
    if len(_channel)!=1:
        raise tellie_exception.TellieException("Cannot fire with >1 channel")
    check_ready()
    cmd = None
    if _channel[0] <= 56: #up to box 7
        cmd = _cmd_fire_average_lower
    else:
        cmd = _cmd_fire_average_upper
    _send_command(cmd, False)
    _firing = True
    _force_setting = False

def fire_single():
    """Fire single pulse
    """
    global _firing
    if _firing is True:
        raise tellie_exception.TellieException("Cannot fire, already in firing mode")
    if _channel <= 56: #up to box 7
        cmd = _cmd_fire_single_lower
    else:
        cmd = _cmd_fire_single_upper
    _send_command(cmd, False)
    _firing = True
    pin = read_pin(_channel[0])
    while not pin:
        pin = read_pin(_channel[0])
    return pin

def fire_continuous():
    """Fire Tellie in continous mode.
    """
    global _firing, _force_setting
    if _firing is True:
        raise tellie_exception.TellieException("Cannot fire, already in firing mode")
    _send_command(_cmd_fire_continuous, False)
    _firing = True
    _force_setting = False

def read_buffer(n=100):
    return _serial.read(n)

def stop():
    """Stop firing tellie"""
    global _firing
    _logger.log(logger.DEBUG, "Stop firing!")
    _send_command(_cmd_stop, False)
    buffer_contents = _serial.read(100)
    _firing = False
    return buffer_contents

def read_pin(channel=None, timeout=2.0, final=True):
    """Read the pin diode output, should always follow a fire command,
    Provide channel number to select specific channel, otherwise, receive dict of all channels"""
    global _firing, _reading
    _logger.log(logger.DEBUG, "Read PINOUT")
    #if in firing mode, check the buffer shows the sequence has ended
    if _firing:
        if _serial.read(100) == _buffer_end_sequence:
            print "K in buffer"
            _firing = False
        else:
            print "No K in buffer"
            return None, None
    if channel:
        if _reading is True:
            if channel != _channel[0]:
                raise tellie_exception.TellieException("Cannot read pin for channel %s, already trying to read channel %s" % (channel, _channel[0]))
        else:
            select_channel(channel)
        if _channel[0] <= 56: #up to box 7
            #cmd = _cmd_read_average_lower
            print "read!"
            cmd = _cmd_read_single_lower
        else:
            #cmd = _cmd_read_average_upper
            print "read!"
            cmd = _cmd_read_single_upper
        if not _reading:
            _send_command(cmd, False)
        pattern = re.compile(r"""\d+""")
        start = time.time()
        pin = []
        while (time.time()-start)<timeout:
            output = _serial.read(100)
            pin = pattern.findall(output)
            if len(pin):
                break
            time.sleep(0.1)
        if len(pin) == 1:
            pin.append(0)
            pin.append(0)
        elif len(pin) != 3:
            _reading = True
            raise tellie_exception.TellieException("Bad number of PIN readouts: %s %s" % (len(pin), pin))
            return None, None
        _reading = False
        if final is True:
            _firing = False
        rms = str(pin[1])+'.'+str(pin[2])
        print pin, rms, channel
        #return str(0)
        return str(pin[0]), rms
    else:
        #check all PINs from the last firing sequence
        #need to store a copy of which pins were read
        channel_list = _channel
        channel_dict = {}
        final_read = False
        for i, channel in enumerate(channel_list):
            if i == len(channel_list)-1:
                final_read = True
            pin, rms,  _ = read_pin(channel, final=final_read)
            channel_dict[channel] = [pin, rms]
        return channel_dict, channel_list

def read_pin_sequence():
    """Read a pin from the sequence firing mode only.
    """
    global _firing
    _logger.log(logger.DEBUG, "Read PINOUT sequence")
    if _firing is not True:
        raise tellie_exception.TellieException("Cannot read pin, not in firing mode")
    pattern = re.compile(r"""\d+""")
    output = _serial.read(100)
    _logger.log(logger.DEBUG, "BUFFER: %s" % output)
    pin = pattern.findall(output)
    if len(pin) == 0:
        pin.append(0)
        pin.append(0)
    elif len(pin) != 3:
        _firing = False
        raise tellie_exception.TellieException("Bad number of PIN readouts: %s %s" % (len(pin), pin))
    elif len(pin) == 0:
        return None, None
    _firing = False
    rms = str(pin[1])+"."str(pin[2])
    channel_dict = {_channel[0]: [pin[0], rms]}
    return channel_dict, _channel
    #return str(pin[0])

def check_ready():
    """Check that all settings have been set"""
    not_set = []
    for channel in _channel:
        if _current_pw[channel-1] is None:
            not_set += ["Pulse width"]
        if _current_ph[channel-1] is None:
            not_set += ["Pulse height"]
        if _current_fd[channel-1] is None:
            not_set += ["Fibre delay"]
    if _current_pn is None:
        not_set += ["Pulse number"]
    if _current_pd is None:
        not_set += ["Pulse delay"]
    if _current_td is None:
        not_set += ["Trigger delay"]
    print not_set
    if not_set != []:
        raise tellie_exception.TellieException("Undefined options: %s" % (", ".join(opt for opt in not_set)))

def clear_channel():
    """Unselect the channel"""
    _logger.log(logger.DEBUG, "Clear channel")
    _send_command(_cmd_channel_clear)
    _channel = []

def clear_channel_settings(channel):
    """Clear settings for a specific channel"""
    global _current_pw, _current_ph, _current_fd
    _current_pw[channel-1] = None
    _current_ph[channel-1] = None
    _current_fd[channel-1] = None

def clear_global_settings():
    """Clear settings that affect all channels"""
    global _current_pn, _current_pd, _current_td
    _current_pn = None
    _current_pd = None
    _current_td = None

def select_channel(channel):
    """Select a channel"""
    global _channel
    if type(channel) is not int:
        channel = int(channel)
    if _channel != []:
        if _channel == [channel]:
            #channel already selected
            return
    _logger.log(logger.DEBUG, "Select channel %s %s" % (channel, type(channel)))
    command = _cmd_channel_select_single_start+chr(channel)+_cmd_channel_select_single_end
    buffer_check = "B"+str((int(channel)-1)/8+1)+_cmd_channel_select_single_end
    _send_command(command=command, buffer_check=buffer_check)
    _channel = [channel]
    return _channel

def select_channels(channels):
    """Select multiple channels, expects list for channels"""
    global _channel
    _logger.log(logger.DEBUG, "Select channels %s %s" % (channels, type(channels)))
    clear_channel()
    command = _cmd_channel_select_many_start
    for channel in channels:
        print channel
        command += chr(channel)
    command += _cmd_channel_select_many_end
    buffer_check = "B"+str((int(channels[0])-1)/8+1)+_cmd_channel_select_many_end
    print "SEND CHANNELS", "CMD", command, "BUF", buffer_check
    _send_command(command=command, buffer_check=buffer_check)
    print "DONE!"
    _channel = channels

def set_pulse_height(par):
    """Set the pulse height for the selected channel"""
    global _current_ph
    if len(_channel) != 1:
        raise tellie_exception.TellieException("Cannot set parameter with channels set as %s" % (_channel))
    if par == _current_ph[_channel[0]] and not _force_setting:
        pass #same as current setting
    else:
        _logger.log(logger.DEBUG, "Set pulse height %s %s" % (par, type(par)))
        command, buffer_check = command_pulse_height(par)
        _send_channel_setting_command(command=command, buffer_check=buffer_check)
        _current_ph[_channel[0]] = par
    return 0

def set_pulse_width(par, while_fire=False):
    """Set the pulse width for the selected channel.
    This is the only setting that can be modified while in firing mode."""
    global _current_pw
    if len(_channel) != 1:
        raise tellie_exception.TellieException("Cannot set parameter with channels set as %s" % (_channel))
    if par == _current_pw[_channel[0]] and not _force_setting:
        pass #same as current setting
    else:
        _logger.log(logger.DEBUG, "Set pulse width %s %s" % (par, type(par)))
        command, buffer_check = command_pulse_width(par)
        if while_fire and _firing:
            _send_channel_setting_command(command=command, while_fire=while_fire)
        else:
            _send_channel_setting_command(command=command, buffer_check=buffer_check)
        _current_pw[_channel[0]] = par
    return 0

def set_fibre_delay(par):
    """Set the fibre (channel) delay for the selected channel"""
    global _current_fd
    if len(_channel) != 1:
        raise tellie_exception.TellieException("Cannot set parameter with channels set as %s" % (_channel))
    if par == _current_fd[_channel[0]] and not _force_setting:
        pass
    else:
        _logger.log(logger.DEBUG, "Set Fibre delay %s %s" % (par, type(par)))
        command, buffer_check = command_fibre_delay(par)
        _send_channel_setting_command(command=command, buffer_check=buffer_check)
        _current_fd[_channel[0]] = par

def set_pulse_number(par):
    """Set the number of pulses to fire (global setting)"""
    global _current_pn
    if par == _current_pn and not _force_setting:
        pass
    else:
        _logger.log(logger.DEBUG, "Set pulse number %s %s" % (par, type(par)))
        command, buffer_check = command_pulse_number(par)
        _send_global_setting_command(command=command, buffer_check=buffer_check)
        _current_pn = par
    return 0

def set_pulse_delay(par):
    """Set the delay between pulses (global setting)"""
    global _current_pd
    if par == _current_pd and not _force_setting:
        pass
    else:
        _logger.log(logger.DEBUG, "Set pulse delay %s %s" % (par, type(par)))
        command, buffer_check = command_pulse_delay(par)
        _send_global_setting_command(command=command, buffer_check=buffer_check)
        _current_pd = par
    return 0

def set_trigger_delay(par):
    """Set the trigger delay (global setting)"""
    global _current_td
    if par == _current_td and not _force_setting:
        pass
    else:
        _logger.log(logger.DEBUG, "Set trigger delay %s %s" % (par, type(par)))
        command, buffer_check = command_trigger_delay(par)
        _send_global_setting_command(command=command, buffer_check=buffer_check)
        _current_td = par
    return 0

def select_temp_probe(par):
    """Select the temperature probe to read"""
    global _current_temp_probe
    if par == _current_temp_probe and not _force_setting:
        pass
    else:
        _logger.log(logger.DEBUG, "Select temperature probe %s %s" % (par, type(par)))
        command, buffer_check = command_select_temp(par)
        _send_command(command=command, readout=False)
        _current_temp_probe = par
        #read the temperature twice
        #first reading is always junk
        #second reading is sometimes junk
        read_temp()
        read_temp()

def read_temp(timeout=1.0):
    """Read the temperature"""
    if not _current_temp_probe:
        raise tellie_exception.TellieException("Cannot read temp: no probe selected")
    cmd = ""
    if _current_temp_probe < 33 and _current_temp_probe > 0:
        cmd = _cmd_temp_read_lower
    elif _current_temp_probe < _max_temp_probe + 1:
        cmd = _cmd_temp_read_upper
    else:
        raise tellie_exception.TellieException("Temp probe not in known range")
    _send_command(command=cmd, readout=False)
    pattern = re.compile(r"""[-+]?\d*\.\d+|\d+""")
    #wait for a few seconds before reading out
    temp = None
    start = time.time()
    while not temp:
        output = _serial.read(100)
        _logger.log(logger.DEBUG, "Buffer: %s" % output)
        temp = pattern.findall(output)
        if time.time() - start > timeout:
            raise tellie_exception.TellieException("Temperature read timeout!")
    if len(temp)>1:
        raise tellie_exception.TellieException("Bad number of temp readouts: %s %s" % (len(temp), temp))
    temp = float(temp[0])
    return temp

def disable_external_trigger():
    """Disable the external trigger"""
    _send_command(command="B")

########################################
# Commands just to check current settings
def get_pulse_delay():
    """Get the pulse delay
    """
    return _current_pd

def get_pulse_number():
    """Get the pulse delay
    """
    return _current_pn
        
##################################################
# Command options and corresponding buffer outputs
#

def command_pulse_height(par):
    """Get the command to set a pulse height"""
    if par > _max_pulse_height or par < 0:
        raise tellie_exception.TellieException("Invalid pulse height: %s" % par)
    hi = par >> 8
    lo = par & 255
    command = [_cmd_ph_hi+chr(hi)]
    command+= [_cmd_ph_lo+chr(lo)]
    command+= [_cmd_ph_end]
    buffer_check = _cmd_ph_hi + _cmd_ph_lo + _cmd_ph_end
    return command, buffer_check


def command_pulse_width(par):
    """Get the command to set a pulse width"""
    if par > _max_pulse_width or par < 0:
        raise tellie_exception.TellieException("Invalid pulse width: %s %s %s" % (par, _max_pulse_width, par>_max_pulse_width))
    hi = par >> 8
    lo = par & 255
    command = [_cmd_pw_hi+chr(hi)]
    command+= [_cmd_pw_lo+chr(lo)+_cmd_pw_end]
    buffer_check = _cmd_pw_hi + _cmd_pw_lo + _cmd_pw_end
    return command, buffer_check


def command_pulse_number(par):
    """Get the command to set a pulse number"""
    if par > _max_pulse_number or par < 0:
        raise tellie_exception.TellieException("Invalid pulse number: %s" % (par))
    par = int(par)
    adjusted, actual_par, hi, lo = parameters.pulse_number(par)
    if adjusted is True:
        raise tellie_exception.TellieException("Invalid pulse number: %s" % (par))
    command = [_cmd_pn_hi+chr(hi)]
    command+= [_cmd_pn_lo+chr(lo)]
    buffer_check = _cmd_pn_hi + _cmd_pn_lo
    return command, buffer_check


def command_pulse_delay(par):
    """Get the command to set a pulse delay"""
    if par > _max_pulse_delay or par < 0:
        raise tellie_exception.TellieException("Invalid pulse delay: %s" % par)
    ms = int(par)
    us = int((par-ms)*250)
    command = [_cmd_pd+chr(ms)]
    command+= [chr(us)]
    buffer_check = _cmd_pd
    return command, buffer_check


def command_trigger_delay(par):
    """Get the command to set a trigger delay"""
    if par > _max_trigger_delay or par < 0:
        raise tellie_exception.TellieException("Invalid trigger delay: %s" % par)
    command = [_cmd_td+chr(par/5)]
    buffer_check = _cmd_td
    return command, buffer_check


def command_fibre_delay(par):
    """Get the command to set a fibre delay"""
    if par > _max_fibre_delay or par < 0:
        raise tellie_exception.TellieException("Invalid fibre delay: %s" % par)
    adjusted, adj_delay, setting = parameters.fibre_delay(par)
    print "COMMAND", par, adjusted, adj_delay, setting
    if adjusted is True:
        raise tellie_exception.TellieException("Invalid delay: %s" % (par))
    command = [_cmd_fd+chr(setting)]
    buffer_check = _cmd_fd
    return command, buffer_check


def command_select_temp(par):
    """Select a temperature probe to read"""
    if par > _max_temp_probe or par < 0:
        raise tellie_exception.TellieException("Invalid temp. probe number: %s" % par)
    cmd = ""
    par = par
    if par < 33 and par > 0:
        cmd = _cmd_temp_select_lower
        par = par
    elif par < _max_temp_probe + 1:
        cmd = _cmd_temp_select_upper
        par = par - 32 #lower
    else:
        raise tellie_exception.TellieException("Invalid temp. probe number: %s" % par)
    command = [cmd+chr(par)]
    return command, None # nothing in buffer


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    # TODO: add some
    args = parser.parse_args()
    initialise_tellie()
    server.register_function(select_channel)
    server.register_function(read_pin_sequence)
    server.register_function(set_pulse_height)
    server.register_function(set_pulse_width)
    server.register_function(set_pulse_number)
    server.register_function(set_pulse_delay)
    server.register_function(set_fibre_delay)
    server.register_function(set_trigger_delay)
    server.register_function(fire_sequence)
    server.register_function(fire_single)
    server.register_function(safe_exit)
    print "serving..."
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "Exiting safely"
        safe_exit()
