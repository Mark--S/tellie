### sends a continuous pulse
from core import serial_command
import sys

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    width = sys.argv[1]
    rate = sys.argv[2]
    number = sys.argv[3]
    width = int(width)
    rate = float(rate)
    number = int(number)
    print width,rate
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTF5YKDL")
    sc.stop()
    sc.select_channel(7)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(rate)
    sc.set_pulse_number(number)
    try:
        sc.fire()
        while True:
            pass
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
        
        
