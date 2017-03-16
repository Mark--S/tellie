#######################
# parameters.py:
#  Any parameters that may need checking
#

import math
import sys
import ConfigParser

# Read config file
config = ConfigParser.ConfigParser()
config.readfp(open('tellie.cfg'))

# Connection to host
_port_name = config.get('CONNECTION', 'port_name')
_server_port = config.getint('CONNECTION', 'server_port')
_logger_port = config.getint('CONNECTION', 'logger_port')
_port_timeout = config.getfloat('CONNECTION', 'port_timeout')

# Parameters for read/write commands
_short_pause = config.getfloat('PARAMETERS', 'short_pause')
_long_pause = config.getfloat('PARAMETERS', 'long_pause')
_read_bytes = config.getfloat('PARAMETERS', 'read_bytes')

# Limitations for pulse settings
_max_pulse_height = config.getint('LIMITATIONS', 'max_pulse_height')
_max_pulse_width = config.getint('LIMITATIONS', 'max_pulse_width')
_max_lo = config.getfloat('LIMITATIONS', 'max_pulse_height')
_max_pulse_delay = config.getfloat('LIMITATIONS', 'max_pulse_delay')
_min_pulse_delay = config.getfloat('LIMITATIONS', 'min_pulse_delay')
_max_trigger_delay = config.getfloat('LIMITATIONS', 'max_trigger_delay')
_max_fibre_delay = config.getfloat('LIMITATIONS', 'max_fibre_delay') # CAUTION: This value was different for serial/server scripts by a factor 2. Setting value conservatively.
_max_pulse_number = config.getint('LIMITATIONS', 'max_pulse_number')
_max_pulse_number_upper = config.getint('LIMITATIONS', 'max_pulse_number_upper')
_max_pulse_number_lower = config.getint('LIMITATIONS', 'max_pulse_number_lower')
_max_temp_probe = config.getfloat('LIMITATIONS', 'max_temp_probe')

# Commands to send to PIC chip on TELLIE
_cmd_fire_continuous = config.get('COMMANDS', 'cmd_fire_continuous')
_cmd_read_single_lower = config.get('COMMANDS', 'cmd_read_single_lower')
_cmd_read_single_upper = config.get('COMMANDS', 'cmd_read_single_upper')
_cmd_fire_average_lower = config.get('COMMANDS', 'cmd_fire_average_lower')
_cmd_fire_average_upper = config.get('COMMANDS', 'cmd_fire_average_upper')
_cmd_fire_series = config.get('COMMANDS', 'cmd_fire_series')
_buffer_end_sequence = config.get('COMMANDS', 'buffer_end_sequence')
_cmd_stop = config.get('COMMANDS', 'cmd_stop')
_cmd_channel_clear = config.get('COMMANDS', 'cmd_channel_clear')
_cmd_channel_select_single_start = config.get('COMMANDS', 'cmd_channel_select_single_start')
_cmd_channel_select_single_end = config.get('COMMANDS', 'cmd_channel_select_single_end')
_cmd_channel_select_many_start = config.get('COMMANDS', 'cmd_channel_select_many_start')
_cmd_channel_select_many_end = config.get('COMMANDS', 'cmd_channel_select_many_end')
_cmd_pulse_height_hi = config.get('COMMANDS', 'cmd_pulse_height_hi')
_cmd_pulse_height_lo = config.get('COMMANDS', 'cmd_pulse_height_lo')
_cmd_pulse_height_end = config.get('COMMANDS', 'cmd_pulse_height_end')
_cmd_pulse_width_hi = config.get('COMMANDS', 'cmd_pulse_width_hi')
_cmd_pulse_width_lo = config.get('COMMANDS', 'cmd_pulse_width_lo')
_cmd_pulse_width_end = config.get('COMMANDS', 'cmd_pulse_width_end')
_cmd_pulse_number_hi = config.get('COMMANDS', 'cmd_pulse_number_hi')
_cmd_pulse_number_lo = config.get('COMMANDS', 'cmd_pulse_number_lo')
_cmd_pulse_delay = config.get('COMMANDS', 'cmd_pulse_delay')
_cmd_trigger_delay = config.get('COMMANDS', 'cmd_trigger_delay')
_cmd_fibre_delay = config.get('COMMANDS', 'cmd_fibre_delay')
_cmd_temp_select_lower = config.get('COMMANDS', 'cmd_temp_select_lower')
_cmd_temp_read_lower = config.get('COMMANDS', 'cmd_temp_read_lower')
_cmd_temp_select_upper = config.get('COMMANDS', 'cmd_temp_select_upper')
_cmd_temp_read_upper = config.get('COMMANDS', 'cmd_temp_read_upper')
_cmd_disable_ext_trig = config.get('COMMANDS', 'cmd_disable_ext_trig')
_cmd_enable_ext_trig = config.get('COMMANDS', 'cmd_enable_ext_trig')
_cmd_fire_average_ext_trig_lower = config.get('COMMANDS', 'cmd_fire_average_ext_trig_lower')
_cmd_fire_average_ext_trig_upper = config.get('COMMANDS', 'cmd_fire_average_ext_trig_upper')
_cmd_fire_ext_trig = config.get('COMMANDS', 'cmd_fire_ext_trig')


def pulse_number(number):
    adjusted = False
    if type(number)!=int:
        raise Exception("PN must be an integer")
    if number > max_pulse_number:
        raise Exception("PN must be < %d.  You set %d" % (_max_pulse_number, number))
        #number = max_pulse_number
        #adjusted = True
    hi = -1
    lo = -1
    diff = 100000 # bigger than max pn
    for i in range(1, 256):
        #assume hi is i
        lo_check = number/i
        if lo_check > _max_pulse_number_lower:
            lo_check = _max_pulse_number_lower
        check = i * lo_check
        if math.fabs(check - number) < diff:
            diff = math.fabs(check - number)
            hi = i
            lo = lo_check
        if check == number:
            break
    actual_par = hi * lo
    if actual_par != number:
        adjusted = True
    return adjusted, actual_par, hi, lo


def trigger_delay(delay):
    adjusted = False
    delay = float(delay)
    if delay > max_trigger_delay or delay < 0:
        raise Exception("TD must be >%s and <%s" % (0, max_trigger_delay))
    parameter = int(round(delay)/5)
    adj_delay = parameter * 5
    if delay != adj_delay:
        adjusted = True
    return adjusted, adj_delay, parameter


def fibre_delay(delay):
    adjusted = False
    delay = float(delay)
    if delay > max_fibre_delay or delay < 0:
        raise Exception("FD must be >%s and <%s" % (0, max_fibre_delay))
    parameter = int(round(delay * 4.))
    adj_delay = float(parameter) / 4.
    if delay != adj_delay:
        adjusted = True
    return adjusted, adj_delay, parameter
