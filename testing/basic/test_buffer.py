#!/usr/bin/env python
#
# test_comms.py
#
# A script to send commands over a serial port.
# Basic (not logic for echoes etc), should
# be able to communicate with all tellie chips.
#
#############################################

from core import serial_command, tellie_exception
import time
import optparse



if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", dest="channel", help="The channel to use",
                      type="int")
    parser.add_option("-p", dest="port", help="Port to run [/dev/tty.usbserial-FTF5YKAZ]",
                      default="/dev/tty.usbserial-FTF5YKAZ")
    parser.add_option("-z", dest="pulse_height", help="Pulse height [10000]",
                      default=10000, type="int")
    parser.add_option("-s", dest="sequence", help="Run in sequence mode?",
                      action="store_true")
    (options, args) = parser.parse_args()

    # initialise the serial connection
    sc = serial_command.SerialCommand(port_name=options.port)

    # select channel also includes the clear channel command - this could be the problem? send a clear at
    # the beginning ONLY!
    print "SELECT CHANNEL"
    sc.select_channel(options.channel)
    print "SET PULSE DELAY"
    sc.set_pulse_delay(100.0)
    print "SET PULSE NUMBER"
    sc.set_pulse_number(100)
    print "SET TRIGGER DELAY"
    sc.set_trigger_delay(0)
    print "SET PULSE HEIGHT"
    sc.set_pulse_height(options.pulse_height)
    print "FIRE!"
    final_buffer = None
    if options.sequence:
        sc.fire_sequence()
        time.sleep(11)
        final_buffer = sc._serial.read(100)
    else:
        sc.fire_continuous()
        time.sleep(10)
        final_buffer = sc.stop()
    print "Buffer contents: ", final_buffer
