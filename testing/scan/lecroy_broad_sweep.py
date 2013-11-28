#!/usr/bin/env python
###################################
# ipw_broad_sweep.py
#
# Runs equivalent scan to LABView IPW
# broad 50 step.  Outputs a waveform
# for each scan, including precursor
# noise information (to ensure offset
# is correct when integrating).
#
# Note that the rate is fixed (1 kHz)
#
###################################

import os
import sys
import optparse
import time
import sweep
import scope

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b", dest="box", help="Box number (1-12)")
    parser.add_option("-c", dest="channel", help="Channel number (1-8)")
    parser.add_option("-x", dest="cutoff", default=12000, help="Cutoff (IPW) from Ref sweep (sweep goes to cutoff + 500)")
    parser.add_option("-p", dest="port", default="/dev/tty.usbserial-FTGDFBHE")
    (options, args) = parser.parse_args()

    #Set parameters
    box = int(options.box)
    channel = int(options.channel)
    cutoff = int(options.cutoff)

    #Fixed parameters
    delay = 1.0 # 1ms -> kHz
    cursor_low = -5e-9 # s
    cursor_high = 23e-9 # s
    trigger_level = 0.5 # half peak minimum
    falling_edge = True
    min_trigger = -0.005 # -5mV smallest allowed trigger

    #run the initial setup on the scope
    lecroy = scope.LeCroy684(True)
    # Don't set the cursors for the measurement - make sure they're setup beforehand!
    #lecroy.set_cursor("x", 1, cursor_low)
    #lecroy.set_cursor("x", 2, cursor_high)
    
    #Create a new, timestamped, summary file
    timestamp = time.strftime("%y%m%d_%H.%M.%S", time.gmtime())
    output_filename = "broad/Box%02d_Channel%d_%s.dat" % (box, channel, timestamp)
    output_file = file(output_filename, 'w')

    output_file.write("#PWIDTH\tPIN\tWIDTH\tRISE\tFALL\tWIDTH\tAREA\n")

    #Start scanning!
    widths = range(0, cutoff+501, 50)
    results = None

    sweep.set_port(options.port)
    sweep.set_scope("LeCroy")
    sweep.start()

    for width in widths:
        min_volt = None
        if results!=None:
            #set a best guess for the trigger and the scale
            #using the last sweeps value
            min_volt = float(results["minimum"])
        results = sweep.sweep("broad", output_filename, box, channel, width, delay, lecroy, min_volt, min_trigger)    
        output_file.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(width, 
                                                      results["pin"], 
                                                      results["width"], 
                                                      results["rise"], 
                                                      results["fall"], 
                                                      results["width"], 
                                                      results["area"]))
    output_file.close()
    
    
