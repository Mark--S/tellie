### sends a continuous pulse
#from core import serial_command
from core.tellie_server import SerialCommand
import sys
import time

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.disable_external_trigger()
    sc.stop()

def read_pin():
    '''Wait keep looking for pin. It will be retuned when the sequence ends
    '''
    pin, rms = None, None
    try:
        while (pin == None):
            pin, rms, channel = sc.read_pin_sequence()
    except KeyboardInterrupt:
        print "Keyboard interrupt"
    except TypeError:
        pin, rms = read_pin()
    return int(pin), float(rms)


if __name__=="__main__":
    width = sys.argv[1]
    #rate = sys.argv[3]
    channel = sys.argv[2]
    width = int(width)
    #rate = float(rate)
    channel = int(channel)
    print width#, rate
    sc = SerialCommand(port_name="/dev/ttyUSB0")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.set_pulse_number(10000)
    #sc.set_pulse_delay(rate)
    sc.set_trigger_delay(0)
    sc.set_fibre_delay(0)
    try:
        print "Enabling external trig"
        sc.enable_external_trig(True)

        print "Trigger Averaged"
        sc.trigger_averaged()
        time.sleep(10)
        pin, __ = read_pin()
        sc.disable_external_trigger()
        sc.stop()
        print "PIN: %s " % pin
        print "___: %s" % __
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
        
        
