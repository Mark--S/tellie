#!/usr/bin/env python
#
########################
#pin_vs_rate:
# Script that creates a file with information
# on the PIN readings vs pulse rate for various
# channels and IPW settings
########################

from core import serial_command
import time

sc = serial_command.SerialCommand()
offset = 19.6e-6 #additional offset in delay

def run_settings(n_pulse,chan,delay,width):
    delay_s = delay*1e-3
    t_run = n_pulse * 1./(delay_s+offset)    
    sc.select_channel(chan)
    sc.set_pulse_number(n_pulse)
    sc.set_pulse_delay(delay)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    sc.fire()
    time.sleep(t_run)
    pin = sc.read_pin()
    while pin==None:
        pin = sc.read_pin()
    return int(pin)

if __name__=="__main__":

    #want to draw pin vs delay for width/chan combo
    tf = ROOT.TFile("pin_delay.root","recreate") 
    #tree for each channel!
    tg = {}
    
    delays = [10.0,3.0,1.0,0.3,0.1]
    widths = [0,1000,2000,3000,4000,
              5000,6000,7000,8000,9000]

    for ibox in range(12):
        box = ibox+1
        for ichan in range(8):

            print "Starting channel: %03d" % chan

            chan = ibox*8 + ichan + 1
            
            tg[chan] = {}
            for width in widths:
                gname = "Chan%03d_Width%05d" %(chan,width)
                tg[chan][width] = ROOT.TGraph()
                tg[chan][width].SetName(gname)

            for delay in delays:
                #run the box for a while first to try to stabalise
                #the temperature
                print "\tdelay: %.3f" % delay

                delay_actual = delay * 1e-3 + offset
                _ = run_settings(n_pulse = 1000,
                                 chan = chan,
                                 delay = delay,
                                 width = 16383)
                for width in widths:
                    pin = run_settings(n_pulse = 1000,
                                       chan = chan,
                                       delay = delay,
                                       width = width)                    
                    pt = tg[chan][width].GetN()
                    tg[chan][width].SetPoint(pt,delay_actual,pin)
    
            for width in widths:
                tg[chan][width].Write()

    tf.Close()
