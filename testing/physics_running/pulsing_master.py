### continuously pulses fibres at 10 Hz during physics runs
import sys
import time
from core.tellie_server import SerialCommand
from common import parameters as p

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

def pulse_channel(width,delay,number,channel):
    width = int(width)
    delay = float(delay)
    number = int(number)
    channel = int(channel)
    sc = SerialCommand(p._serial_port)
    sc.stop()
    sc.select_channel(channel)
    sc.set_trigger_delay(0)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(delay)
    sc.set_pulse_number(number)
    try:
        sc.fire_sequence()
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

if __name__=="__main__":
    WIDTH = p._max_pulse_width      # IPW (TODO: read from ratDB)
    RATE = 10                       # Hz (TODO: add parameter)
    NUM  = 10                       # Number of pulses
    CHAN = (6,7,8)                  # Channels on Sussex test bench
    print "Will try to pulse each channel %d times at %f Hz" % (NUM, RATE)
    delay = float(1.e-3/RATE)       # ms
    for ch in CHAN:
        print "Attempting to pulse channel %d" % ch
        pulse_channel(WIDTH,delay,NUM,ch) 
        print "Successfully pulsed channel %d" % ch
        time.sleep(p._long_pause)
        print "-----"
    print "SUCCESS"

