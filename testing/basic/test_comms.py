#!/usr/bin/env python
#
# test_comms.py
#
# A script to send commands over a serial port.
# Basic (not logic for echoes etc), should
# be able to communicate with all tellie chips.
#
#############################################

import serial
import time
import optparse

def clear_channel(s):
    """Clear things!
    """
    print "clear settings"
    cmd = "C"
    s.write(cmd)
    time.sleep(0.1)
    return cmd

def select_channel(s, channel):
    """Just select the channel.
    """
    print "selecting channel: %s" % channel
    cmd = "I" + chr(channel) + "N"  # select channel
    s.write(cmd)
    time.sleep(0.1)
    return cmd


def set_pulse_height(s, height):
    """Set the pulse height.
    0 - 16383
    """
    print "setting pulse height: %s" % height
    hi = height >> 8
    lo = height & 255
    cmd = "L" + chr(hi) + "M" + chr(lo) + "P"
    s.write(cmd)
    time.sleep(0.1)
    return cmd

def set_pulse_delay(s, delay):
    """Set the pulse delay.
    250.0 - 0.001
    """
    print "setting pulse delay: %s ms" % delay
    ms = int(delay)
    us = int((delay - ms)*250)
    cmd = "u" + chr(ms) + chr(us)
    s.write(cmd)
    time.sleep(0.1)
    return cmd

def set_pulse_number(s, hi, lo):
    """Set the pulse number.
    PN = hi * lo.
    Hi: 1 - 255
    Lo: 1 - 255
    """
    print "setting pulse number: %s" % (hi * lo)
    cmd = "H" + chr(hi) + "G" + chr(lo)
    s.write(cmd)
    time.sleep(0.1)
    return cmd

def set_trigger_delay(s, delay):
    """Set the trigger delay.
    delay * 5 ns.
    """
    print "setting the trigger delay: %s ns" % (delay * 5)
    cmd = "d" + chr(delay)
    s.write(cmd)
    time.sleep(0.1)
    return cmd

def fire_continuous(s, seconds):
    """Fire a continuous pulse for n seconds
    """
    print "firing in continuous mode"
    time.sleep(0.1) # ensure all parameter settings have loaded
    try:
        s.write("a")
        time.sleep(seconds)
        s.write("X") # stop!
    except:
        print "Pulsing interrupted! stopping"
        s.write("X")
    print "stopped"

def fire_sequence(s):
    """Fire the loaded sequence
    """
    print "firing in sequence mode"
    time.sleep(0.1) # ensure all parameter settings have loaded
    s.write("g") # just a sequence fire command
    print "will continue to fire using the settings (number * delay) requested"


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", dest="channel", help="The channel to use",
                      type="int")
    parser.add_option("-p", dest="port", help="Port to run [/dev/tty.usbserial-FTF5YKAZ]",
                      default="/dev/tty.usbserial-FTE3C0PG")
    parser.add_option("-z", dest="pulse_height", help="Pulse height [10000]",
                      default=10000, type="int")
    parser.add_option("-s", dest="sequence", help="Run in sequence mode?",
                      action="store_true")
    (options, args) = parser.parse_args()
    # initialise the serial connection
    s = serial.Serial(port=options.port, timeout=0.5)

    #setup the board
    cmd = ""
    cmd += clear_channel(s)
    cmd += set_pulse_delay(s, 10.0) # 10ms delay -> 100 Hz
    cmd += set_pulse_number(s, 10, 10) # run 100 pulses, no effect for continuous mode
    cmd += set_trigger_delay(s, 0) # no delay
    cmd += select_channel(s, options.channel)
    cmd += set_pulse_height(s, options.pulse_height)
    
    if options.sequence:
        fire_sequence(s)
    else:
        fire_continuous(s, 10) # run for 10 seconds
    # finally, just check what was in the buffer
    print "Commands sent:", cmd
    time.sleep(10)
    print "Buffer contents:", s.read(100)
