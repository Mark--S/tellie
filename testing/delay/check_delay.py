### sends a continuous pulse
from core import serial_command
import scope_connections
import scopes
import utils
import sys

usb_conn = scope_connections.VisaUSB()
scope = scopes.Tektronix3000(usb_conn)

sc = serial_command.SerialCommand()
sc.stop()

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":

    #CHANGE ME IF YOU NEED TO SET THRESHOLDS!
    scope.lock()
    scope.set_single_acquisition()
    scope.set_edge_trigger(-0.03,2,True)
#    scope.set_data_mode(4990,7000)
    data_start = 4990
    data_stop = 7000
    scope._connection.send("wfmpre:pt_fmt y") # Single point format
    scope._connection.send("data:encdg ribinary") # Signed int binary mode
    scope._connection.send("data:start %i" % data_start) # Start point
    scope._data_start = data_start
    scope._connection.send("data:stop %i" % data_stop) # 100000 is full 
    scope.lock()

    # setup the scope and fire
    chan = raw_input("select channel (to fire): ")
    box_name = raw_input("set actual box number: ")
    chan_name = raw_input("set the actual channel number (1-8): ")
    chan = int(chan)
    box_name = int(box_name)
    chan_name = int(chan_name)
    sc.select_channel(chan)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(0)
    sc.set_pulse_delay(1.1) #no zeros on the new chip!
    sc.set_pulse_number(257) #no zeros on the new chip!
    sc.fire()

    # create an output file and save
    fname = "results/Waveform_Box%02d_Chan%02d" % (box_name,chan_name)
    results = utils.PickleFile(fname,2)
    results.set_meta_data("timeform_1",scope.get_timeform(1))
    results.set_meta_data("timeform_2",scope.get_timeform(2))
    results.add_data(scope.get_waveform(1),1)
    results.add_data(scope.get_waveform(2),2)
    results.save()
    results.close()

    scope.unlock()

        
