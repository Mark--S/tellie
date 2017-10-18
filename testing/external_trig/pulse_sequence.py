### sends a continuous pulse
from core.tellie_server import SerialCommand
import sys
from common import parameters as p

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()
    sys.exit()

if __name__=="__main__":
    width = sys.argv[1]
    number = sys.argv[2]
    channel = sys.argv[3]
    width = int(width)
    number = int(number)
    channel = int(channel)
    #print width,number,channel
    sc = SerialCommand(p._serial_port)
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    sc.set_pulse_number(number)
    try:
        sc.trigger_averaged()
    except Exception,e:
        safe_exit(sc,e)

    mean = None
    try:
        print "Waiting for sequence to finish..."
        while (mean == None):
            try:
                mean, rms, chan = sc.read_pin_sequence()
            except TypeError:
                mean = None
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc, "keyboard interrupt")

    print "\nPIN: %s \nRMS: %s\n" % (mean, rms)
        
        
