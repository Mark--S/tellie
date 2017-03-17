from core import serial_command
import os
import sys
import optparse
import time
import scopes
import scope_connections
import sweep
import math
from common import parameters as p

_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,1000]

def l(sc, c, n, sp, i):
    po, rms = None, None
    sc.set_pulse_number(n)
    sc.fire_sequence()
    while po is None:
        po, rms, cl = sc.read_pin_sequence()
    r = {}
    r["t"] = time.time() - i
    r["a"] = (sp.measure(1,"area"))
    r["r"] = (sp.measure(1,"rise"))
    r["f"] = (sp.measure(1,"fall"))
    r["w"] = (sp.measure(1,"nwidth"))
    r["p"] = po[channel]
    return r


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", dest="channel", type="int", help="Channel number")
    parser.add_option("-w", dest="width", type="int", help="Pulse width")
    parser.add_option("-p", dest="port", help="Serial port")
    (options, args) = parser.parse_args()

   #Fixed parameters                                                                                                                                                                 
    delay = 1.0 # 1ms -> kHz                                                                                                                                        
    cursor_low = -5e-9 #s                                                                                                  
    cursor_high = 23e-9 # s                                                                                                                                           
    trigger_level = 0.5 # half peak minimum
    falling_edge = True
    min_trigger = -0.005 # -5mV smallest allowed trigger

    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    scope.set_cursor("x",1,cursor_low)
    scope.set_cursor("x",2,cursor_high)

    sc = serial_command.SerialCommand(options.port)


    # Channel parameters
    height = p._max_pulse_height
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = p._pulse_num
    delay = 1
    channel =  options.channel
    width = options.width

    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    output_filename = "light/Channel%d_Width%d_%s.dat" % (channel,width,timestamp)
    output_file = file(output_filename,'w')
    output_file.write("#PTIME\tWIDTH\tPIN\tWIDTH\tRISE\tFALL\tAREA\n")

    
    # Set up scope
        #first, run a single acquisition with a forced trigger, effectively to clear the waveform
    scope.set_single_acquisition()
    time.sleep(p._short_pause) #needed for now to get the force to work...
    scope._connection.send("trigger:state ready")
    time.sleep(p._short_pause)
    scope._connection.send("trigger force")
    time.sleep(p._short_pause)

    #if no trigger settings, run a test fire
    min_volt = sweep.get_min_volt(channel,height,width,
                                delay,scope,min_trigger=min_trigger)
    min_volt = sweep.get_min_volt(channel,height,width-75,
                                delay,scope,min_trigger=min_trigger)

    sc.select_channel(channel)
    sc.set_pulse_width(width)
    sc.set_pulse_height(height)
    sc.set_fibre_delay(fibre_delay)
    sc.set_pulse_delay(delay)
    sc.set_trigger_delay(trigger_delay)

    #set the trigger level to half the minimum value (and ensure a good scale)
    trigger = min_volt / 2
    if trigger > min_trigger:
        trigger = min_trigger
    volts_div = math.fabs(min_volt*4 ) # 6 divs total, plus some leaway
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


    # Start pulsing

    # Setup the initial settings
    sc.select_channel(options.channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_trigger_delay(0)
    sc.set_fibre_delay(0)
    sc.set_pulse_delay(p._min_pulse_delay)
    
    stop = 1
    # Loop over lots of times...
    c = options.channel
    sp = scope
    z = width
    o = output_file
    i = time.time()
    while stop != 0:
        r = l(sc, c, 1, sp, i)
        o.write("%f\t%d\t%s\t%s\t%s\t%s\t%s\n"%(r["t"],
                                                     z,
                                                     r["p"],
                                                     r["w"],
                                                     r["r"],
                                                     r["f"],
                                                     r["a"]))
    output_file.close()
