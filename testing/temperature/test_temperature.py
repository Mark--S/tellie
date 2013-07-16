### sends a continuous pulse
from core import serial_command, tellie_exception
from common import tellie_logger
import sys

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")
    sc.stop()
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(True)
    try:
        while True:
            probe = raw_input("Select a sensor to probe: ")
            try:
                probe = int(probe)
            except ValueError:
                print "Must select a numerical probe!"
                continue
            sc.select_temp_probe(probe)
            try:
                temp = sc.read_temp()
                print "Temperature: %s C"%temp
            except tellie_exception.TellieException,e:
                print "Error reading temperature"
                print e
                continue
    except Exception,e:
        safe_exit(sc,e)
    except KeyboardInterrupt:
        safe_exit(sc,"keyboard interrupt")
        
        
