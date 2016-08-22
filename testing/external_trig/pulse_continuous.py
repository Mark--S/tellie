### sends a continuous pulse
from core import serial_command
import sys

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    width = int(sys.argv[1])
    channel = int(sys.argv[2])

    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTGA2OCZ")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)

    try:
        sc.enable_external_trig()
        while True:
            pass
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
