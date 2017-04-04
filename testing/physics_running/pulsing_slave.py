### continuously pulses fibres during physics runs (externally triggered)
import sys
import time
from core.tellie_server import SerialCommand
from common import parameters as p

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()
    sys.exit()

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

def pulse_channel(sc,width,number,channel):
    width = int(width)
    number = int(number)
    channel = int(channel)
    sc.stop()
    sc._clear_buffer()  # just in case
    sc.clear_channel()
    time.sleep(p._short_pause)
    sc.select_channel(channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    sc.set_pulse_number(number)
    try:
        sc.trigger_averaged()
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
    
    # Get PIN readout
    mean = None
    try:
        mean, rms = read_pin()
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc, "keyboard interrupt")
    print "\nPIN: %s \nRMS: %s\n" % (mean, rms)

# Main function has hard-coded values, just for testing at the moment
if __name__=="__main__":
    sc = SerialCommand(p._serial_port)
    WIDTH = p._max_pulse_width      # IPW (TODO: read from ratDB)
    NUM  = 1000                     # Number of pulses per channel
    CHAN = (6,7,8)                  # Channels on Sussex test bench
    print "\nINFO - Will try to pulse each channel %d times (externally triggered)\n" % (NUM)
    for ch in CHAN:
        print "INFO - Attempting to pulse channel %d\n" % ch
        pulse_channel(sc,WIDTH,NUM,ch) 
        print "INFO - Successfully pulsed channel %d\n" % ch
        time.sleep(p._medium_pause)
    print "INFO - SUCCESS - ALL CHANNELS FIRED\n"

