### sends a continuous pulse
from core import serial_command
import sys

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()
    sys.exit()

if __name__=="__main__":
    width = int(sys.argv[1])
    number = int(sys.argv[2])
    channel = int(sys.argv[3])

    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTGA2OCZ")
    sc.stop()
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
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
            mean, rms, chan = sc.read_pin_sequence()
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc, "keyboard interrupt")

    print "\nPin: %s \nrms: %s\n" % (mean, rms)
