### sends a continuous pulse
import sys
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
            try:
                pin, rms, channel = sc.read_pin_sequence()
            except TypeError:
                pin = None
    except KeyboardInterrupt:
        print "Keyboard interrupt"
    except TypeError:
        pin, rms = read_pin()
    return int(pin), float(rms)

if __name__=="__main__":
    width = int(sys.argv[1])
    delay = float(sys.argv[2])
    number = int(sys.argv[3])
    channel = int(sys.argv[4])
    sc = SerialCommand(p._serial_port)   # set in tellie.cfg
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

    mean = None
    try:
        mean, rms = read_pin()
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc, "keyboard interrupt")

    print "\nPIN: %s \nRMS: %s\n" % (mean, rms)
