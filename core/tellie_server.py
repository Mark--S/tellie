#!/usr/bin/env python
#
# tellie_server
#
# classes: SerialCommand
#          TellieException
#          TellieSerialException
#          ThreadException
#
# Launches a xmlrpc server containing the 
# SerialCommand class used to talk to the 
# tellie control box. 
#
# Author: EdLeming
#         <e.leming@sussex.ac.uk>
#
###########################################
###########################################
from SimpleXMLRPCServer import SimpleXMLRPCServer
import serial
import tellie_exception
import re
import sys
import time
import math
from common import parameters as p
#from core import serial_command as s
_snotDaqLog = False
try:
    from snotdaq import logger
    _snotDaqLog = True
except ImportError:
    _snotDaqLog = False

from common import tellie_logger

class TellieException(Exception):
    """General exception for the Tellie command modules"""

    def __init__(self, error):
        Exception.__init__(self, error)


class TellieSerialException(Exception):
    """Exception when communicating with the Serial Port"""

    def __init__(self, error):
        Exception.__init__(self, error)


class ThreadException(Exception):
    """Exception raised specific to threading issues"""

    def __init__(self, error):
        Exception.__init__(self, error)


class SerialCommand(object):
    """Contains a serial command object.
    """
    
    # ####################
    # Function for easier logging
    def log_phrase(self, phrase, severity=0, isSnotDaqLog=False):
        if (severity == 0):
            if isSnotDaqLog:
                self.logger.debug(phrase)
            self.logger_local.debug(phrase)
        elif (severity == 1):
            if isSnotDaqLog:
                self.logger.notice(phrase)
            self.logger_local.notice(phrase)
        elif (severity == 2):
            if isSnotDaqLog:
                self.logger.warn(phrase)
            self.logger_local.warn(phrase)
        else:
            self.logger.warn("Severity of log_phrase not set correctly: %d" % severity)
    
    def parse_hex(self, string):
        result = ""
        data = list(string)
        for c in data:
            if not c.isalpha(): r = '[%d]' % ord(c)    # not in alphabet, assume hex
            else:               r = c                  # leave as is
            result = result + r + " "
        return result

    def __init__(self, serial_port = p._serial_port, server_port = p._server_port, logger_port = p._logger_port, port_timeout = p._port_timeout):
        '''Initialise function: open serial connection.
        '''
        self._serial_port = serial_port
        self._port_timeout = port_timeout
        self._logger_port = logger_port
        
        #Setting local log file on snodrop
        self.logger_local = tellie_logger.TellieLogger.get_instance()
        self.logger_local.set_log_file(p._server_log)
        self.logger_local.set_debug_mode(True)
        
        # Set up logger stuff.
        if _snotDaqLog:
            self.logger = logger.Logger()
            self.logger.set_verbosity(2)
            try:
                self.logger.connect('tellie', 'minard', self._logger_port)
            except Exception as e:
                self.logger.warn("unable to connect to log server: %s" % str(e))
            self.logger.notice("Tellie connected to log server!")
        
        # Set up serial connection to tellie
        self._serial = None
        try:
            self._serial = serial.Serial(port=p._serial_port,timeout=p._port_timeout)
            self.log_phrase("Serial connection open: %s" % self._serial, 0, _snotDaqLog)
        except serial.SerialException, e:
            raise TellieSerialException(e)

        # Cache current settings - remove need to re-command where possible
        # Channel specific settings
        self._channel = [] #always a list
        self._current_pulse_width = [-999]*96
        self._current_pulse_height = [-999]*96
        self._current_fibre_delay = [-999]*96

        # Global settings
        self._current_pulse_number = None
        self._current_pulse_delay = None
        self._current_trigger_delay = None

        # Information on whether the channel is being fired
        self._firing = 0 #must wait for firing to complete
        self._reading = 0 #once a read command has been sent, dont send again!

        # Temperature settings
        self._current_temp_probe = None

        # If a new channel is selected should force setting all new parameters
        # restriction only lifted once a fire command has been called
        self._force_setting = False

        # Send a reset, to ensure the RTS is set to false
        self.reset()
        self.pulse_single_init_server()
        # Send a clear channel command, just in case
        self._clear_buffer()
        self.clear_channel()

        #By default stop tellie waiting for external trigger (i.e. running in slave mode).
        #Slave mode can be re-instated later if required.
        self.disable_external_trigger()

    def __del__(self):
        """Deletion function"""
        self.reset()
        self.clear_channel()
        if self._serial:
            self.disable_external_trigger()
            self._serial.close()
        
        self.disconnect()
        self.log_phrase("tellie server dropped out", 2, _snotDaqLog)
    
    def disconnect(self):
        """Disconnect from USB serial port"""
        if self._serial:
            self._serial.close()

    def test(self):
        self.log_phrase("Tellie server responding", 1, _snotDaqLog)

    def _clear_buffer(self):
        """Clear any chars left in the buffer"""
        buffer_read = self.read_buffer()
        if buffer_read != "":
            self.log_phrase("Buffer was not clear: %s" % buffer_read, 0, _snotDaqLog)

    def _check_clear_buffer(self):
        """Many commands expect an empty buffer, fail if they are not!
        """
        buffer_read = self.read_buffer()
        if buffer_read != "":
            # serial command class raised a TellieException instead
            if _snotDaqLog:
                self.logger.warn("Buffer not clear: %s" % (buffer_read))
            self.logger_local.warn("Buffer not clear: %s" % (buffer_read))

    def _send_command(self, command, readout=True, buffer_check=None, sleep_after_command=p._short_pause):
        """Send a command to the serial port.
        Command can be a chr/str (single write) or a list.
        Lists are used for e.g. a high/low bit command where
        the high bit could finish with an endline (i.e. endstream)

        sleep_after_command is the default time to sleep between each write command"""
        self.log_phrase("_send_command:%s" % command, 0, _snotDaqLog)

        if type(command) is str:
            command = [command]
        if type(command) is not list:
            raise TellieException("Command is not a list: %s %s" % (command, type(command)))
        #try:
        for c in command:
            self.log_phrase("Writing chars %s" % self.parse_hex(c), 0, _snotDaqLog)
            bytesWritten = self._serial.write(c)
            self.log_phrase("Written chars %s" % self.parse_hex(c), 0, _snotDaqLog)
            self.log_phrase("Bytes written %d" % bytesWritten, 0, _snotDaqLog)
            time.sleep(sleep_after_command)
        #except Exception as e:
        #    raise TellieException("Lost connection with TELLIE hardware! Re-set server")

        if not buffer_check: # assume returns same as input
            buffer_check = ''
            for c in command:
                buffer_check += c

        if readout is True:
            # One read command (with default timeout of 0.1s) should be
            # enough to get all the chars from the readout.
            buffer_read = self._serial.read(len(buffer_check))
            attempt = 0
            self.log_phrase("READ: %s\tCHECK: %s" % (buffer_read, buffer_check), 0, _snotDaqLog)
            while (len(buffer_read) != len(buffer_check)) and attempt<10:
                self.log_phrase("Didn't read correct no of chars, read again", 0, _snotDaqLog)
                # First, try reading again
                time.sleep(p._short_pause)
                buffer_read += self._serial.read(len(buffer_check))
                attempt += 1

            if str(buffer_read)!=str(buffer_check):
                self.log_phrase("problem reading buffer, send %s, read %s" % (command, buffer_read), 0, _snotDaqLog)
                #clear anything else that might be in there
                time.sleep(p._short_pause)
                remainder = self.read_buffer()
                self._serial.write(p._cmd_stop) # send a stop
                time.sleep(p._short_pause)
                self._serial.write(p._cmd_channel_clear) # send a clear
                time.sleep(p._short_pause)
                self.read_buffer()
                if buffer_read == '\x00':
                    self.log_phrase("Looks like power was lost to tellie...It may still be off?", 2, _snotDaqLog)
                    # Re-run 
                    self._send_command(command, readout, buffer_check, sleep_after_command)
                message = "Unexpected buffer output:\nsaw: %s, remainder %s\nexpected: %s\n" % (buffer_read, remainder, buffer_check)
                self.log_phrase(message, 2, _snotDaqLog)
                self.disable_external_trigger()
                self.clear_channel()
                raise TellieException(message)
            else:
                self.log_phrase("success reading buffer: %s" % buffer_read, 0, _snotDaqLog)
        else:
            self.log_phrase("not a readout command", 0, _snotDaqLog)

    def _send_setting_command(self, command, buffer_check=None, while_fire=False):
        """Send non-firing command.
        All of these should have a clear buffer before being used.  Can set
        while_fire to True to allow a non-fire command to be sent while firing
        (will cause PIN readout to be flushed to buffer).
        """
        self.log_phrase("Send non-firing command", 0, _snotDaqLog)
        if self._firing is True:
            if while_fire is False:
                raise TellieException("Cannot run command, in firing mode")
            else:
                #Assume that we CANNOT readout the buffer here!
                self._send_command(command=command, readout=False)
        else:
            self._check_clear_buffer()
            self._send_command(command=command, buffer_check=buffer_check)

    def _send_global_setting_command(self, command, buffer_check=None, while_fire=False):
        """Send non-firing command that affects all channels.
        Can set while_fire to True to allow a non-fire command to be sent
        while firing (will cause PIN readout to be flushed to buffer).
        """
        self.log_phrase("Send global setting command %s" % (command), 0, _snotDaqLog)
        self._send_setting_command(command=command, buffer_check=buffer_check, while_fire=while_fire)

    def _send_channel_setting_command(self, command, buffer_check=None, while_fire=False):
        """Send non-firing command for specific channel.
        Can set while_fire to True to allow a non-fire command to be sent while
        firing (will cause PIN readout to be flushed to buffer).
        """
        self.log_phrase("Send channel setting command %s" % (command), 0, _snotDaqLog)

        if not self._channel or self._channel == []:
            raise TellieException("Cannot run channel command, no channel selected")
        if len(self._channel)!=1:
            raise TellieException("Cannot run channel command, must have single channel selected: %s" % (self._channel))
        self._send_setting_command(command=command, buffer_check=buffer_check, while_fire=while_fire)

    def reset(self):
        """Send a reset command!

        Assumes that the port is open (which it is by default)
        """
        self.log_phrase("Reset!", 0, _snotDaqLog)        

        self._serial.setRTS(True)
        # sleep, just in case
        time.sleep(p._medium_pause)
        self._serial.setRTS(False)
        # close the port and reopen?
        time.sleep(p._medium_pause)
        self.disable_external_trigger()

    def enable_external_trig(self, while_fire=False):
        """Tell TELLIE to fire on any external trigger.

        Can send a fire command while already in fire mode if required."""
        self.log_phrase("Enable ext triggering mode", 0, _snotDaqLog)
        if self._firing is True and while_fire is False:
            self.log_phrase("Cannot set ext. trig, already in firing mode", 2, _snotDaqLog)
            return  # I think this required a hard reset in ORCA, maybe remove?
        self._send_command(p._cmd_enable_ext_trig)

    def disable_external_trigger(self):
        """Disable the external trigger"""
        self._send_command(command=p._cmd_disable_ext_trig)

    def trigger_single(self):
        """Fire single pulse upon receiving an external trigger.

        """
        if self._firing is True:
            raise TellieException("Cannot fire, already in firing mode")
        self._send_command(p._cmd_fire_ext_trig, False)
        self._firing = True
        time.sleep(p._short_pause)
        pin = self.read_pin(self._channel[0])
        while not pin:
            pin = self.read_pin(self._channel[0])
        return pin

    def trigger_averaged(self):
        """Request averaged pin reading for externally triggered pulses."""
        self.log_phrase("Accepting %i triggers for averaging!" % self._current_pulse_number, 0, _snotDaqLog)
        if len(self._channel)!=1:
            self.log_phrase("Cannot fire with >1 channel! Averaging request denied.", 2, _snotDaqLog)
            return
        if self._firing is True:
            self.log_phrase("Already in firing mode! Averaging request denied.", 2, _snotDaqLog)
            return
        if self._channel[0] <= 56: #up to box 7     (NOTE: serial_command.py did NOT have the index!)
            cmd = p._cmd_fire_average_ext_trig_lower
        else:
            cmd = p._cmd_fire_average_ext_trig_upper
        self._send_command(cmd, False)
        self._firing = True

    def fire(self, while_fire=False):
        """Fire tellie, place class into firing mode.
        Can send a fire command while already in fire mode if required."""
        self.log_phrase("Fire!", 0, _snotDaqLog)
        self.disable_external_trigger()
        if self._firing is True and while_fire is False:
            raise TellieException("Cannot fire, already in firing mode")
        self.check_ready()
        # Set readout to false when firing (must read
        # averaged pin at some later time).
        cmd = None
        buffer_check = p._cmd_fire_series
        #if the series is less than 0.5 seconds, also check for the end of sequence
        if (self._current_pulse_number * self._current_pulse_delay) < 500:
            buffer_check += _buffer_end_sequence
            self._send_command(p._cmd_fire_series, buffer_check=buffer_check)
        else:
            self._send_command(p._cmd_fire_series, buffer_check=buffer_check)
            self._firing = True #still firing
        self._force_setting = False

    def fire_sequence(self, while_fire=False):
        """Fire in sequence mode, can only be done for a single channel.
        """
        self.log_phrase("Fire sequence!", 0, _snotDaqLog)
        self.disable_external_trigger()
        if len(self._channel)!=1:
            self.log_phrase("Cannot fire with >1 channel!", 2, _snotDaqLog)
            return 0
        if self._current_pulse_number == 0:
            self.log_phrase("Requested to fire 0 pulses!", 2, _snotDaqLog)
            return 0
        self.check_ready()
        cmd = None
        if self._channel[0] <= 56: #up to box 7
            cmd = p._cmd_fire_average_lower
        else:
            cmd = p._cmd_fire_average_upper
        self._send_command(cmd, False)
        self._firing = True
        self._force_setting = False

    def fire_single(self):
        """Fire single pulse
        """
        self.disable_external_trigger()
        if self._firing is True:
            raise TellieException("Cannot fire, already in firing mode")
        if self._channel[0] <= 56: #up to box 7
            cmd = p._cmd_fire_single_lower
        else:
            cmd = p._cmd_fire_single_upper
        self._send_command(cmd, False)
        self._firing = True
        pin = self.read_pin(self._channel[0])
        while not pin:
            pin = self.read_pin(self._channel[0])
        return pin

    def fire_continuous(self):
        """Fire Tellie in continous mode.
        """
        self.disable_external_trigger()
        if self._firing is True:
            raise TellieException("Cannot fire, already in firing mode")
        self._send_command(p._cmd_fire_continuous, False)
        self._firing = True
        self._force_setting = False

    def read_buffer(self, n=p._read_bytes):
        return self._serial.read(n)

    def stop(self):
        """Stop firing tellie"""
        self.log_phrase("Stop firing!", 0, _snotDaqLog)
        #Disable external trigger before we do anything
        self.disable_external_trigger()
        self.clear_channel()
        for c in self._channel:
            self.clear_channel_settings(c)
        self.clear_global_settings()
        self._channel = []
        self._send_command(p._cmd_stop, False)
        time.sleep(p._short_pause)
        buffer_contents = self.read_buffer()
        self._firing = False
        return buffer_contents

    def read_pin(self, channel=None, timeout=p._medium_pause, final=True):
        """Read the pin diode output, should always follow a fire command,
        Provide channel number to select specific channel, otherwise, receive dict of all channels"""
        self.log_phrase("Read PINOUT", 0, _snotDaqLog)
        #if in firing mode, check the buffer shows the sequence has ended
        if self._firing:
            if self.read_buffer() == _buffer_end_sequence:
                print "K in buffer"
                self._firing = False
            else:
                print "No K in buffer"
                return None, None
        if channel:
            if self._reading is True:
                if channel != self._channel[0]:
                    raise TellieException("Cannot read pin for channel %s, already trying to read channel %s" % (channel, self._channel[0]))
            else:
                self.select_channel(channel)
            if self._channel[0] <= 56: #up to box 7
                print "read!"
                cmd = p._cmd_read_single_lower
            else:
                print "read!"
                cmd = p._cmd_read_single_upper
            if not self._reading:
                self._send_command(cmd, False)
            pattern = re.compile(r"""\d+""")
            start = time.time()
            pin = []
            while (time.time()-start)<timeout:
                output = self.read_buffer()
                pin = pattern.findall(output)
                if len(pin):
                    break
                time.sleep(p._short_pause)
            if len(pin) == 0:
                self._reading = True
                return None, None
            elif len(pin) == 1:
		        pin.append(0)
		        pin.append(0)
            else:
                self._firing = False
                self._reading = False
                raise TellieException("Bad number of PIN readouts: %s %s" % (len(pin), pin))
            self._reading = False
            if final is True:
                self._firing = False
            return pin[0], channel
            # May want to include RMS values:
	        #rms_val = str(pin[1])+"."+str(pin[2])
            #return pin[0],rms_val, channel
        else:
            #check all PINs from the last firing sequence
            #need to store a copy of which pins were read
            channel_list = self._channel
            channel_dict = {}
            final_read = False
            for i, channel in enumerate(channel_list):
                if i == len(channel_list)-1:
                    final_read = True
                pin, _ = self.read_pin(channel, final=final_read)
                channel_dict[channel] = pin
                # May want to include RMS values:
                #pin, rms_val, _ = self.read_pin(channel, final=final_read)
                #channel_dict[channel] = [pin,rms_val]
            return channel_dict, channel_list

    def read_pin_sequence(self):
        """Read a pin from the sequence firing mode only.
        """
        self.log_phrase("Read PINOUT sequence", 0, _snotDaqLog)
        if self._firing is not True:
            raise TellieException("Cannot read pin, not in firing mode")
        time.sleep(0.2)
        output = self.read_buffer()
        
        self.log_phrase("BUFFER: %s" % output, 0, _snotDaqLog)
        numbers = output.split()
        if len(numbers) == 0:
            self.log_phrase("Sequence doesn't appear to have finished..", 0, _snotDaqLog)
            return None
        elif len(numbers) == 2:
            try:
                pin = float(numbers[0])
                rms = float(numbers[1])
            except:
                self.log_phrase("Unable to convert numbers to floats Numbers: %s Buffer: %s",str(numbers),output, 2, _snotDaqLog)
                return None

        else:
            self.log_phrase("Bad number of PIN readouts: %s %s" % (len(numbers), numbers), 2, _snotDaqLog)
            return None
        self._firing = False
        value_dict = {self._channel[0]: pin}
        rms_dict = {self._channel[0]: rms}
        return pin, rms, self._channel

    def check_ready(self):
        """Check that all settings have been set"""
        not_set = []
        for channel in self._channel:
            if self._current_pulse_width[channel-1] is None:
                not_set += ["Pulse width"]
            if self._current_pulse_height[channel-1] is None:
                not_set += ["Pulse height"]
            if self._current_fibre_delay[channel-1] is None:
                not_set += ["Fibre delay"]
        if self._current_pulse_number is None:
            not_set += ["Pulse number"]
        if self._current_pulse_delay is None:
            not_set += ["Pulse delay"]
        if self._current_trigger_delay is None:
            not_set += ["Trigger delay"]
        if not_set != []:
            self.log_phrase("The following parameters have not been set: %s" % not_set, 0, _snotDaqLog)

    def clear_channel(self):
        """Unselect the channel"""
        self.log_phrase("Clear channel", 0, _snotDaqLog)
        self._send_command(p._cmd_channel_clear)
        self._channel = []

    def clear_channel_settings(self, channel):
        """Clear settings for a specific channel"""
        self._current_pulse_width[channel-1] = None
        self._current_pulse_height[channel-1] = None
        self._current_fibre_delay[channel-1] = None

    def clear_global_settings(self):
        """Clear settings that affect all channels"""
        self._current_pulse_number = None
        self._current_pulse_delay = None
        self._current_trigger_delay = None

    def select_channel(self, channel):
        """Select a channel"""
        if type(channel) is not int:
            channel = int(channel)
        if self._channel != []:
            if self._channel == [channel]:
                #channel already selected
                self.log_phrase("Channel already selected", 0, _snotDaqLog)
                return 0
        self.log_phrase("Select channel %s %s" % (channel, type(channel)), 0, _snotDaqLog)
        command, buffer_check = command_select_channel(channel)
        self.log_phrase("About to send command %s, %s" % (command, buffer_check), 0, _snotDaqLog)
        self._send_command(command=command, buffer_check=buffer_check)
        self._channel = [channel]
        self.log_phrase("About to return", 0, _snotDaqLog)
        return 0 # OK status

    def select_channels(self, channels):
        """Select multiple channels, expects list for channels"""
        self.log_phrase("Select channels %s %s" % (channels, type(channels)), 0, _snotDaqLog)
        self.clear_channel()
        command = p._cmd_channel_select_many_start
        for channel in channels:
            print channel
            command += chr(channel)
        command += p._cmd_channel_select_many_end
        buffer_check = p._cmd_disable_ext_trig+str((int(channels[0])-1)/8+1)+p._cmd_channel_select_many_end
        print "SEND CHANNELS", "CMD", command, "BUF", buffer_check
        self._send_command(command=command, buffer_check=buffer_check)
        print "DONE!"
        self._channel = channels

    def init_channel(self, channel, pulse_number, pulse_delay, trigger_delay,
                     pulse_width, pulse_height, fibre_delay):
        """Select and setup all channel settings.
        """
        self.log_phrase("inside init_channel", 0, _snotDaqLog)
        if self._firing:
            self.log_phrase("Currently in firing mode. Wait until firing has stopped before retrying channel init.", 0, _snotDaqLog)
            return 1
        #####
        # Not included here: large block of command/buffer check outputs from serial_command.py
        #####
        self.select_channel(int(channel))
        self.set_pulse_number(int(pulse_number))
        self.set_pulse_delay(float(pulse_delay))
        self.set_trigger_delay(int(trigger_delay))
        self.set_pulse_width(int(pulse_width))
        self.set_pulse_height(int(pulse_height))
        self.set_fibre_delay(float(fibre_delay))

        # Return a dump of the settings
        settings = {"channels": self._channel,
                    "pulse_number": self._current_pulse_number,
                    "pulse_delay": self._current_pulse_delay,
                    "trigger_delay": self._current_trigger_delay,
                    "channel_settings": {}}
        for c in self._channel:
            settings["channel_settings"][str(c)] = {"pulse_width": self._current_pulse_width[c],
                                                    "pulse_height": self._current_pulse_height[c],
                                                    "fibre_delay": self._current_fibre_delay[c]}
        return settings

    def set_pulse_height(self, par):
        """Set the pulse height for the selected channel"""
        if len(self._channel) != 1:
            raise TellieException("Cannot set parameter with channels set as %s" % (self._channel))
        if par == self._current_pulse_height[self._channel[0]] and not self._force_setting:
            self.log_phrase("Pulse height: %s,already set" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set pulse height %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_pulse_height(par)
            self._send_channel_setting_command(command=command, buffer_check=buffer_check)
            self._current_pulse_height[self._channel[0]] = par
        return 0

    def set_pulse_width(self, par):
        """Set the pulse width for the selected channel.
        This is the only setting that can be modified while in firing mode."""
        if len(self._channel) != 1:
            raise TellieException("Cannot set parameter with channels set as %s" % (self._channel))
        if par == self._current_pulse_width[self._channel[0]] and not self._force_setting:
            self.log_phrase("Pulse width: %s, already set" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set pulse width %s %s" % (par, type(par)), 0, _snotDaqLog)            
            command, buffer_check = command_pulse_width(par)
            self._send_channel_setting_command(command=command, buffer_check=buffer_check)
            self._current_pulse_width[self._channel[0]] = par
        return 0

    def set_fibre_delay(self, par):
        """Set the fibre (channel) delay for the selected channel"""
        if len(self._channel) != 1:
            raise TellieException("Cannot set parameter with channels set as %s" % (self._channel))
        if par == self._current_fibre_delay[self._channel[0]] and not self._force_setting:
            self.log_phrase("Fibre delay %s, already selected" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set Fibre delay %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_fibre_delay(par)
            self._send_channel_setting_command(command=command, buffer_check=buffer_check)
            self._current_fibre_delay[self._channel[0]] = par
        return 0

    def set_pulse_number(self, par):
        """Set the number of pulses to fire (global setting)"""
        if par == self._current_pulse_number and not self._force_setting:
            self.log_phrase("Number of pulses: %s already selected" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set pulse number %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_pulse_number(par)
            self._send_global_setting_command(command=command, buffer_check=buffer_check)
            self._current_pulse_number = par
        return 0

    def set_pulse_delay(self, par):
        """Set the delay between pulses (global setting)"""
        if par == self._current_pulse_delay and not self._force_setting:
            self.log_phrase("Pulse delay: %s, already selected" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set pulse delay %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_pulse_delay(par)
            self._send_global_setting_command(command=command, buffer_check=buffer_check)
            self._current_pulse_delay = par
        return 0

    def set_trigger_delay(self, par):
        """Set the trigger delay (global setting)"""
        if par == self._current_trigger_delay and not self._force_setting:
            self.log_phrase("Trigger delay: %s,already set" % (par), 0, _snotDaqLog)
        else:
            self.log_phrase("Set trigger delay %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_trigger_delay(par)
            self._send_global_setting_command(command=command, buffer_check=buffer_check)
            self._current_trigger_delay = par
        return 0

    def select_temp_probe(self, par):
        """Select the temperature probe to read"""
        if par == self._current_temp_probe and not self._force_setting:
            pass
        else:
            self.log_phrase("Select temperature probe %s %s" % (par, type(par)), 0, _snotDaqLog)
            command, buffer_check = command_select_temp(par)
            self._send_command(command=command, readout=False)
            self._current_temp_probe = par
            #read the temperature twice
            #first reading is always junk
            #second reading is sometimes junk
            self.read_temp()
            self.read_temp()
        return 0

    def read_temp(self, timeout=p._medium_pause):
        """Read the temperature"""
        if not self._current_temp_probe:
            raise TellieException("Cannot read temp: no probe selected")
        cmd = ""
        if self._current_temp_probe < 33 and self._current_temp_probe > 0:
            cmd = p._cmd_temp_read_lower
        elif self._current_temp_probe < p._max_temp_probe + 1:
            cmd = p._cmd_temp_read_upper
        else:
            raise TellieException("Temp probe not in known range")
        self._send_command(command=cmd, readout=False)
        pattern = re.compile(r"""[-+]?\d*\.\d+|\d+""")
        #wait for a few seconds before reading out
        temp = None
        start = time.time()
        while not temp:
            output = self.read_buffer()
            self.log_phrase("Buffer: %s" % output, 0, _snotDaqLog)
            temp = pattern.findall(output)
            if time.time() - start > timeout:
                raise TellieException("Temperature read timeout!")
        if len(temp)>1:
            raise TellieException("Bad number of temp readouts: %s %s" % (len(temp), temp))
        temp = float(temp[0])
        return temp

    #Method to do the single pulse when starting the server
    def pulse_single_init_server(self):
        self.select_channel(1)
        self.set_pulse_number(1)
        self.set_pulse_delay(0)
        self.set_trigger_delay(0)
        self.set_pulse_width(p._max_pulse_width)
        self.set_pulse_height(p._max_pulse_height)
        self.set_fibre_delay(0.0)
        self.fire_sequence()
        mean, rms, chan = self.read_pin_sequence()
        self.stop()
        self.clear_channel()

    ########################################
    # Commands just to check current settings
    def get_pulse_delay(self):
        """Get the pulse delay
        """
        return self._current_pulse_delay

    def get_pulse_number(self):
        """Get the pulse delay
        """
        return self._current_pn
        
##################################################
# Command options and corresponding buffer outputs
#
# These are retained such that command chains may
# be called (e.g. set all settings) before running
# a buffer readout.

def command_select_channel(par):
    """Get the command to select a single channel"""
    command = [p._cmd_channel_select_single_start+chr(par)+p._cmd_channel_select_single_end]
    buffer_check = p._cmd_disable_ext_trig+str((int(par)-1)/8+1)+p._cmd_channel_select_single_end
    return command, buffer_check


def command_pulse_height(par):
    """Get the command to set a pulse height"""
    if par > p._max_pulse_height or par < 0:
        raise TellieException("Invalid pulse height: %s" % par)
    hi = par >> 8   # binary right shift
    lo = par & 255  # binary AND operator
    command = [p._cmd_pulse_height_hi+chr(hi)]
    command+= [p._cmd_pulse_height_lo+chr(lo)]
    command+= [p._cmd_pulse_height_end]
    buffer_check = p._cmd_pulse_height_hi + p._cmd_pulse_height_lo + p._cmd_pulse_height_end
    return command, buffer_check


def command_pulse_width(par):
    """Get the command to set a pulse width"""
    if par > p._max_pulse_width or par < 0:
        raise TellieException("Invalid pulse width: %s %s %s" % (par, p._max_pulse_width, par>p._max_pulse_width))
    hi = par >> 8   # binary right shift
    lo = par & 255  # binary AND operator
    command = [p._cmd_pulse_width_hi+chr(hi)]
    command+= [p._cmd_pulse_width_lo+chr(lo)+p._cmd_pulse_width_end]
    buffer_check = p._cmd_pulse_width_hi + p._cmd_pulse_width_lo + p._cmd_pulse_width_end
    return command, buffer_check


def command_pulse_number(par):
    """Get the command to set a pulse number"""
    if par > p._max_pulse_number or par < 0:
        raise TellieException("Invalid pulse number: %s" % (par))
    par = int(par)
    #parameters  = ParametersClass()
    adjusted, actual_par, hi, lo = p.pulse_number(par)
    if adjusted is True:
        raise TellieException("Invalid pulse number: %s" % (par))
    command = [p._cmd_pulse_number_hi+chr(hi)]
    command+= [p._cmd_pulse_number_lo+chr(lo)]
    buffer_check = p._cmd_pulse_number_hi + p._cmd_pulse_number_lo
    return command, buffer_check


def command_pulse_delay(par):
    """Get the command to set a pulse delay"""
    if par > p._max_pulse_delay or par < 0:
        raise TellieException("Invalid pulse delay: %s" % par)
    ms = int(par)
    us = int((par-ms)*250)
    command = [p._cmd_pulse_delay+chr(ms)]
    command+= [chr(us)]
    buffer_check = p._cmd_pulse_delay
    return command, buffer_check


def command_trigger_delay(par):
    """Get the command to set a trigger delay"""
    if par > p._max_trigger_delay or par < 0:
        raise TellieException("Invalid trigger delay: %s" % par)
    command = [p._cmd_trigger_delay+chr(par/5)]
    buffer_check = p._cmd_trigger_delay
    return command, buffer_check


def command_fibre_delay(par):
    """Get the command to set a fibre delay"""
    if par > p._max_fibre_delay or par < 0:
        raise TellieException("Invalid fibre delay: %s" % par)
    #parameters = ParametersClass()
    adjusted, adj_delay, setting = p.fibre_delay(par)
    print "COMMAND", par, adjusted, adj_delay, setting
    if adjusted is True:
        raise TellieException("Invalid delay: %s" % (par))
    command = [p._cmd_fibre_delay+chr(setting)]
    buffer_check = p._cmd_fibre_delay
    return command, buffer_check


def command_select_temp(par):
    """Select a temperature probe to read"""
    if par > p._max_temp_probe or par < 0:
        raise TellieException("Invalid temp. probe number: %s" % par)
    cmd = ""
    par = par
    if par < 33 and par > 0:
        cmd = p._cmd_temp_select_lower
        par = par
    elif par < p._max_temp_probe + 1:
        cmd = p._cmd_temp_select_upper
        par = par - 32 #lower
    else:
        raise TellieException("Invalid temp. probe number: %s" % par)
    command = [cmd+chr(par)]
    return command, None # nothing in buffer


##################################################
# Helper functions (was only needed in serial_command)
#def command_append(inputs, values):
#    '''Pass in inputs as (command, buffer_check) and values to append.
#
#    Inputs should be a list.
#    Command should be returned as a list, buffer_check as a string.
#    '''
#    assert len(inputs) == len(values)
#    if type(inputs[0]) is not list:
#        inputs[0] = [inputs[0]]
#    if type(values[0]) is not list:
#        inputs[0] += [values[0]]
#    else:
#        inputs[0] += values[0]
#    inputs[1] = "%s%s" % (inputs[1], values[1])
#    return inputs

if __name__ == "__main__":
    runTime = time.time()
    server = SimpleXMLRPCServer(("0.0.0.0", p._server_port), allow_none=True)

    tellieCommands = SerialCommand()
    server.register_instance(tellieCommands, allow_dotted_names=True)
    
    print "serving..."
    print "Setup time was: %f" % (time.time()-runTime)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "Exiting..."
