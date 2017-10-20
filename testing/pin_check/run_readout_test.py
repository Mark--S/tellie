#!/usr/bin/env python
##############################
# run_readout_test.py
#
# Script to run pin readings from a specified
# channel, multiple times.  User provides
# the number of shots to fire (average over)
#
##############################

import time
import optparse
from core.tellie_server import SerialCommand
from common import parameters as p

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c",dest="channel")
    parser.add_option("-w",dest="width")
    parser.add_option("-n",dest="number")
    parser.add_option("-l",dest="label",default=None)
    parser.add_option("-p",dest="port",default=None)
    (options, args) = parser.parse_args()
    channel = int(options.channel)
    width = int(options.width)
    number = int(options.number)
    #defaults
    readings = 20
    delay = 1.0
    rate = 1./(delay*1e-3 + 200e-6)        
    t_wait = 1./rate + 0.1#add 100ms just to be sure
    #setup board
    sc = tellie_server.SerialCommand(options.port)
    sc.select_channel(channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    sc.set_fibre_delay(0)
    sc.set_pulse_delay(p._pulse_delay)
    sc.set_trigger_delay(0)    
    sc.set_pulse_number(number)
    #outputs
    #fname = "check_results/PIN_%s_%02d_%03d_%05d.dat" % (options.label,channel,number,width)
    #fout = file(fname,"w")
    for i in range(readings):
        #sc.fire_single()
        sc.fire_sequence()
        time.sleep(t_wait)
        pin, rms = None, None
        ntries = 0
        while pin is None:
            time.sleep(p._short_pause)
            try:
                pin, rms,  _ = sc.read_pin_sequence()
            except TypeError:
                pin = None
            ntries += 1 
            print ntries, pin
            if ntries>5:
                break
        #fout.write("%s\n"%pin[channel])
        print "reading %s: PIN %s +/- %s"%(i,pin[channel],rms[channel])
    #fout.close()
    
