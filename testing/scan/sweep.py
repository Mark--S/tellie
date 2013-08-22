#!/usr/bin/env python
#########################
# sweep.py
#  Generic module for running
# IPW sweeps with both a scope
#
#########################

import os
from core import serial_command
import scopes
import math
import time
import utils
import sys

port = "/dev/tty.usbserial-FTE3C0PG"
_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,1000]

#initialise sc here, faster options setting
sc = serial_command.SerialCommand(port)

def get_min_volt(channel,height,width,delay,scope,scale=None,trigger=None,min_trigger=-0.005):
    """Gets the trigger settings by firing a single pulse
    """
    sc.select_channel(channel)
    sc.set_pulse_height(height)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(delay)
    sc.set_pulse_number(1)
    if scale==None or trigger==None:
        scope.set_y_scale(1,1) # set to 1V/Div initially
        scope.set_edge_trigger(-0.5,1,True)
    else:
        #check the scale and trigger are reasonable
        set_scale = scale
        test_trigger = trigger
        for i,t in enumerate(_v_div):
            if scale > t:
                set_scale = _v_div[i]
        if trigger > min_trigger:
            trigger = min_trigger
        scope.set_y_scale(1,set_scale)
        scope.set_edge_trigger(trigger,1,True)
    scope.set_single_acquisition()
    scope.lock()
    sc.fire()
    pin = None
    while pin==None:
        pin = sc.read_pin()
    #single pulse fired, read from the scope  
    min_volt = float(scope.measure(1,"minimum"))
    scope.unlock()
    return min_volt
    

def sweep(dir_out,file_out,box,channel,width,delay,scope,min_volt=None,min_trigger=-0.005):
    """Perform a measurement using a default number of
    pulses, with user defined width, channel and rate settings.
    """
    print '____________________________'
    print width
    #fixed options
    height = 16383    
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = 1000
    #first select the correct channel and provide settings
    logical_channel = (box-1)*8 + channel

    #first, run a single acquisition with a forced trigger, effectively to clear the waveform
    scope.set_single_acquisition()
    time.sleep(0.1) #needed for now to get the force to work...
    scope._connection.send("trigger:state ready")
    time.sleep(0.1)
    scope._connection.send("trigger force")
    time.sleep(0.1)

    #if no trigger settings, run a test fire
    if min_volt==None:
        min_volt = get_min_volt(logical_channel,height,width,
                                delay,scope,min_trigger=min_trigger)

    sc.select_channel(logical_channel)
    sc.set_pulse_width(width)
    sc.set_pulse_height(16383)
    sc.set_pulse_delay(delay)
    sc.set_fibre_delay(fibre_delay)
    sc.set_trigger_delay(trigger_delay)
  
    #set the trigger level to half the minimum value (and ensure a good scale)
    trigger = min_volt / 2
    if trigger > min_trigger:
        trigger = min_trigger
    volts_div = math.fabs(min_volt / 4) # 6 divs total, plus some leaway
    volts_div_setting = None
    #find the correct volts/div
    for i,t in enumerate(_v_div):
        if volts_div > t:
            if i<(len(_v_div)-2):
                volts_div_setting = _v_div[i+1]
            else:
                volts_div_setting = _v_div[-2]
    if volts_div_setting ==None:
        volts_div_setting = _v_div[0] # set to minimal
    print "VDIV",volts_div,volts_div_setting

    scope.set_y_scale(1,volts_div_setting)
    scope.set_edge_trigger(trigger,1,True)
    scope.set_average_acquisition(1000)
    scope.lock()
    sc.set_pulse_number(pulse_number)

    sc.fire()
    #wait for the sequence to end
    tsleep = pulse_number * (delay*1e-3 + 210e-6)
    time.sleep(tsleep) #add the offset in
    pin = None
    while pin==None:
        pin = sc.read_pin()
    #should now have an averaged waveform
    directory = "%s/channel_%2d"%(dir_out,logical_channel)
    if not os.path.exists(directory):
        os.makedirs(directory)
    ## create an output file and save
    fname = "%s/Chan%02d_Width%05d" % (directory,logical_channel,width)
    waveform = scope.get_waveform(1)
    if waveform!=None:
        results = utils.PickleFile(fname,1)
        results.set_meta_data("timeform_1",scope.get_timeform(1))
        results.add_data(waveform,1)    
        results.save()
        results.close()
    else:
        print "SKIPPING WAVEFORM FOR WIDTH",width
    #have saved a waveform, now save rise,fall,pin etc
    
    results = {}

    results["area"] = (scope.measure(1,"area")) 
    results["rise"] = (scope.measure(1,"rise")) 
    results["fall"] = (scope.measure(1,"fall")) 
    results["width"] = (scope.measure(1,"nwidth")) 
    results["minimum"] = (scope.measure(1,"minimum"))
    results["pin"] = pin

    scope.unlock()

    return results
