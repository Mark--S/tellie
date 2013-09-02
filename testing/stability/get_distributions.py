import os
import sys
import waveform_tools as wt
from core import serial_command
import scopes
import scope_connections
import math
import time
import utils
import optparse

_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,1000]
sc = serial_command.SerialCommand()

def get_min_volt(channel,height,width,delay,scope,scale=None,trigger=None,min_trigger=-0.005):
    """Gets the trigger settings by firing a single pulse
    """
    sc.select_channel(channel)
    sc.set_pulse_height(height)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(delay)
    sc.set_pulse_number(10)
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
    time.sleep(0.1)
#    sc.fire()
#    pin = None
#    while pin==None:
#        pin = sc.read_pin()
    pin = sc.fire_single()
    #single pulse fired, read from the scope  
    min_volt = float(scope.measure(1,"minimum"))
    scope.unlock()
    return min_volt

def measure(box,channel,width,delay,scope,min_volt=None,min_trigger=-0.005):
    """Perform a measurement using a default number of
    pulses, with user defined width, channel and rate settings.
    """
    #fixed options
    height = 16383    
    fibre_delay = 0
    trigger_delay = 0
#    pulse_number = 1
    pulse_number = 10
    #first select the correct channel and provide settings
    logical_channel = (box-1)*8 + channel

#    #first, run a single acquisition with a forced trigger, effectively to clear the waveform
#    scope.set_single_acquisition()
#    time.sleep(0.1) #needed for now to get the force to work...
#    scope._connection.send("trigger:state ready")
#    time.sleep(0.1)
#    scope._connection.send("trigger force")
#    time.sleep(0.1)


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

    scope.set_y_scale(1,volts_div_setting)
    scope.set_edge_trigger(trigger,1,True)
    scope.set_single_acquisition()
#    scope.set_average_acquisition(8)
    scope.lock()
    sc.set_pulse_number(pulse_number)

    #sc.fire()
    pin = sc.fire_single()
    #wait for the sequence to end
    #tsleep = pulse_number * (delay*1e-3 + 210e-6)
    #pin = None
    #time.sleep(tsleep)
    #while pin==None:
    #    pin = sc.read_pin()
    
    results = {}

    results["area"] = (scope.measure(1,"area")) 
    results["pin"] = pin

    scope.unlock()

    return results


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    (options,args) = parser.parse_args()

    #Set parameters
    box = int(options.box)
    channel = int(options.channel)


    #Fixed parameters
    delay = 1.0 # 1ms -> kHz
    cursor_low = -5e-9 # s
    cursor_high = 23e-9 # s
    trigger_level = 0.5 # half peak minimum
    falling_edge = True
    min_trigger = -0.005 # -5mV smallest allowed trigger

    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    scope.set_cursor("x",1,cursor_low)
    scope.set_cursor("x",2,cursor_high)
    
    #Create a new, timestamped, summary file
    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    widths = [0,2000,4000,6000,7000]
    last_scale = None
    last_trigger = None
    for width in widths:
        if width==6000:
            last_scale = 0.2
            last_trigger = -0.1
        elif width==7000:
            last_scale = 0.1
            last_trigger = -0.04
        print width
        pins = []
        photons = []
        output_filename = "Box%02d_Channel%d_Width%d_%s.dat" % (box,channel,width,timestamp)
        output_file = file(output_filename,"w")

        logical_channel = (box-1)*8 + channel
        min_volt = get_min_volt(logical_channel,16383,width,
                                0.1,scope,scale=last_scale,trigger=last_trigger)
        last_scale = -min_volt
        last_trigger = min_volt/20

        for i in range(200):

            if(i%10)==0:
                print "\t",i
            results = measure(box,channel,width,delay,scope,min_volt=min_volt)
            output_file.write("%s\t%s\t%s\n"%(width,
                                              results["pin"],
                                              results["area"]))
        output_file.close()
