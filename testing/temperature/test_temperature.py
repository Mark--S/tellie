### sends a continuous pulse
import sys
from core import tellie_exception
from common import tellie_logger
from core.tellie_server import SerialCommand
from common import parameters as p

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    sc = SerialCommand(p._serial_port)   # set in tellie.cfg
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
        
        
