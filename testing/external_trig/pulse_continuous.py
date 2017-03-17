### sends a continuous pulse
from core.tellie_server import SerialCommand
import sys
import time
from common import parameters as p

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    width = sys.argv[1]
    channel = sys.argv[2]
    width = int(width)
    #rate = float(rate)     # external trigger
    channel = int(channel)
    #print width
    sc = SerialCommand(p._serial_port)
    #sc.stop()
    print "SELECTING CHANNEL"
    time.sleep(p._long_pause)
    sc.select_channel(channel)
    print "SELECTED CHANNEL"
    time.sleep(p._long_pause)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    try:
        sc.enable_external_trig()
        while True:
            pass
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")

