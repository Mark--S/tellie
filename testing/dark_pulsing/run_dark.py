from core import tellie_server
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

def send_pulses_dark(sc, channel, width, number):
    sc.select_channel(channel)
    sc.set_pulse_width(width)
    sc.set_pulse_number(number)
    sc.fire_sequence()
    # Need to know when to read the pin    
    sequence_time = sc.get_pulse_delay() * sc.get_pulse_number() # ms
    time.sleep((sequence_time + 0.2) * 0.001) # Add 200us offset
    pin_out, rms = None, None
    while pin_out is None:
        pin_out, rms, channel_list = sc.read_pin_sequence()

def send_pulses_light(sc, channel, width, number, scope, init_time):
    sc.select_channel(channel)
    sc.set_pulse_width(width)
    sc.set_pulse_number(number)
    sc.fire_sequence()
    # Need to know when to read the pin    
    sequence_time = sc.get_pulse_delay() * sc.get_pulse_number() # ms
    time.sleep((sequence_time + 0.2) * 0.001) # Add 200us offset
    pin_out, rms = None, None
    while pin_out is None:
        pin_out, rms, channel_list = sc.read_pin_sequence()
    
    results = {}
    results["time"] = float(time.time()) - float(init_time)
    results["area"] = (scope.measure(1,"area"))
    results["rise"] = (scope.measure(1,"rise"))
    results["fall"] = (scope.measure(1,"fall"))
    results["width"] = (scope.measure(1,"nwidth"))
    results["minimum"] = (scope.measure(1,"minimum"))
    results["pin"] = pin_out[channel]
    results["pin_rms"] = rms[channel]
    print results
    scope.unlock()
    return results


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", dest="channel", type="int", help="Channel number")
    parser.add_option("-w", dest="width", type="int", help="Pulse width")
    parser.add_option("-p", dest="port", help="Serial port")
    (options, args) = parser.parse_args()

    # Fixed parameters
    delay = 1.0 # 1ms -> kHz
    cursor_low = -5e-9 #s
    cursor_high = 23e-9 # s
    trigger_level = 0.5 # half peak minimum
    falling_edge = True
    min_trigger = -0.005 # -5mV smallest allowed trigger

    # Run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)
    scope.set_cursor("x",1,cursor_low)
    scope.set_cursor("x",2,cursor_high)

    sc = tellie_server.SerialCommand(options.port)


    # Channel parameters
    height = p._max_pulse_height
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = p._pulse_num
    delay = 0.001
    channel = options.channel
    width = options.width

    timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    output_filename = "dark/Channel%d_Width%d_%s.dat" % (channel,width,timestamp)
    output_file = file(output_filename,'w')
    output_file.write("#PTIME\tWIDTH\tPIN\tWIDTH\tRISE\tFALL\tWIDTH\tAREA\n")

    
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
    min_volt = sweep.get_min_volt(channel,height,width,
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


    # Start pulsing

    # Setup the initial settings
    sc.select_channel(options.channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_trigger_delay(0)
    sc.set_fibre_delay(0)
    sc.set_pulse_delay(0.001)
    
    stop = 1
    # Loop over lots of times...
    init_time = time.time()
    while stop != 0:
        send_pulses_dark(sc, options.channel, p._max_pulse_height, p._pulse_num)
        results = send_pulses_light(sc, options.channel, options.width, 1, scope, init_time)
        output_file.write("%f\t%d\t%s\t%s\t%s\t%s\t%s\t%s\n"%(results["time"],
                                                          width,
                                                          results["pin"],
                                                          results["pin_rms"],
                                                          results["width"],
                                                          results["rise"],
                                                          results["fall"],
                                                          results["width"],
                                                          results["area"]))
    output_file.close()
