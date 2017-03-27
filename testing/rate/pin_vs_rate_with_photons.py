#!/usr/bin/env python
#
########################
#pin_vs_rate:
# Script that creates a file with information
# on the PIN readings vs pulse rate for various
# channels and IPW settings
########################

import scopes
import scope_connections
import ROOT
import time
import optparse
import scope_actions
from core.tellie_server import SerialCommand
from common import parameters as p


#for the branches
ROOT.gROOT.ProcessLine(\
    "struct Results{\
        Int_t width;\
        Int_t pin;\
        Float_t scope_area;\
        Float_t delay;\
        Float_t delay_actual;\
     };")
from ROOT import Results
results = Results()


usb_conn = scope_connections.VisaUSB()
scope = scopes.Tektronix3000(usb_conn)

sc = SerialCommand()
offset = 200e-6 #additional offset in delay

def run_settings(n_pulse,chan,delay,width):
    delay_s = delay*1e-3
    t_run = n_pulse * (delay_s+offset)    
    sc.select_channel(chan)
    sc.set_pulse_number(n_pulse)
    sc.set_pulse_delay(delay)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_width(width)
    sc.fire()
    time.sleep(t_run)
    pin = sc.read_pin()
    while pin==None:
        pin = sc.read_pin()
    return int(pin)

if __name__=="__main__":

    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box")
    parser.add_option("-c",dest="channel")
    (options,args) = parser.parse_args()

    box = int(options.box)
    channel = int(options.channel)

    logical_channel = (box-1)*8 + channel

    #want to draw pin vs delay for width/chan combo
    tf = ROOT.TFile("pin_delay_photons_box%02d_channel%02d.root"%(box,channel),"recreate")

    tt = ROOT.TTree("tree","tree")
    tt.Branch("width",ROOT.AddressOf(results,"width"),"width/I")
    tt.Branch("pin",ROOT.AddressOf(results,"pin"),"pin/I")
    tt.Branch("delay",ROOT.AddressOf(results,"delay"),"delay/F")
    tt.Branch("delay_actual",ROOT.AddressOf(results,"delay_actual"),"delay_actual/F")
    tt.Branch("scope_area",ROOT.AddressOf(results,"scope_area"),"scope_area/F")

    delays = [100.0,50.0,30.0,20.0,10.0,5.0,3.0,2.0,1.0,0.5,0.3,0.2,0.1]
    widths = [8100,8000,7000,6000,5000,4000,3000,2000,1000,0]

    #setup the scope
    scope.set_cursor("x",1,-5e-9)
    scope.set_cursor("x",2,23e-9)

    for width in widths:

        print "RUNNING WIDTH",width

        #get the scope trigger settings here
        #voltage settings depend ENTIRELY on the board
        if width>8000:            
            scope.set_y_scale(1,0.01)
            scope.set_edge_trigger(-0.008,1,True)
        elif width>7000:            
            scope.set_y_scale(1,0.1)
            scope.set_edge_trigger(-0.02,1,True)
        elif width>5000:
            scope.set_y_scale(1,0.2)
            scope.set_edge_trigger(-0.1,1,True)
        else:
            scope.set_y_scale(1,1)
            scope.set_edge_trigger(-0.5,1,True)

        time.sleep(p._short_pause)
            
        scope.set_single_acquisition()
        _ = run_settings(n_pulse = 10,
                         chan = logical_channel,
                         delay = 100.0,
                         width = width)
        min_volt = float(scope.measure(1,"minimum"))
        print "MIN",min_volt

        #assume that the amplitude can double
        v_div = scope_actions.get_volts_div(-min_volt) # 6 divs available, but use a larger setting
        trigger = min_volt/2
        if trigger>-0.01:
            trigger=-0.01
        scope.set_y_scale(1,v_div)
        scope.lock()

        for delay in delays:

            scope.set_average_acquisition(32)
            #add a jitter on the trigger to ensure a new readout
            scope.set_edge_trigger(min_volt,1,True)
            scope.set_edge_trigger(min_volt/2,1,True)
            #run the box for a while first to try to stabalise
            #the temperature
            print "\tdelay: %.3f" % delay

            delay_actual = delay * 1e-3 + offset

            _ = run_settings(n_pulse = 100,
                             chan = logical_channel,
                             delay = delay,
                             width = width)
            pin = run_settings(n_pulse = 100,
                               chan = logical_channel,
                               delay = delay,
                               width = width)

            area = float(scope.measure(1,"area"))

            results.width = width
            results.pin = pin
            results.delay = delay * 1e-3
            results.delay_actual = delay_actual
            results.scope_area = area

            tt.Fill()

        scope.unlock()

    tt.Write()
    tf.Close()
