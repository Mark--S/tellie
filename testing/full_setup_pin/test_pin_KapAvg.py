#!/usr/bin/env python

import time
import ROOT
import numpy
from core import serial_command
import sys

#sc = serial_command.SerialCommand('/dev/ttyS0')
sc = serial_command.SerialCommand('/dev/tty.usbserial-FTGA2OCZ')

channels = range(1,25)

try:
    channels = [int(sys.argv[1])]
    print "RUNNING CHANNEL",channels
except:
    pass
#channels = [10]
#channels = [60]
#channels = []
#for i in range(4):
#    channels.append(i*4+1)
#channels = [60,65,70,75]
print channels

#widths = range(0,6000,200)
#heights = range(0, 6000, 300)
#heights = [0,10,20,30,40,50,60,70,80,90]
#heights = [100,100,100,100,100,100,100,100,100,100]

heights = range(0, 16000, 1000)

#######################################
#for the branches
ROOT.gROOT.ProcessLine(\
    "struct Results{\
        Int_t height;\
        Int_t pin_avg;\
        Int_t pin_std;\
     };")
from ROOT import Results
results = Results()
########################################

tc = ROOT.TCanvas("can","can")


sc.select_channel(channels[0])
sc.set_pulse_height(16383)
sc.set_pulse_delay(1.0)
sc.set_pulse_number(500)
sc.set_fibre_delay(0)
sc.set_trigger_delay(0)
sc.disable_external_trigger()
sc.set_pulse_width(16383)
sc.fire()
time.sleep(1)
pin = None
while pin==None:
    pin = sc.read_pin()
print "DARK FIRE OVER: PIN",pin
time.sleep(1)

noReads=50
pinReads = range(1, noReads)
pinReadArr = numpy.zeros(( noReads ))
for channel in channels:

    print "running channel",channel
    
    t_str = time.strftime('%y%m%d_%H.%M')
    #fname = "~/tellie/testing/full_setup_pin/CalibResults/test/pin_height_ch%02d_%s.root"%(channel,t_str)
    fname = "~/tellie/testing/full_setup_pin/CalibResults/Linearity_Full_Errors_b1_500p/ch%02d.root"%(channel)
    tf = ROOT.TFile(fname,"recreate")

    tt = ROOT.TTree("T","T")
    tt.Branch("height",ROOT.AddressOf(results,"height"),"height/I")
    tt.Branch("pin_avg",ROOT.AddressOf(results,"pin_avg"),"pin_avg/I")
    tt.Branch("pin_std",ROOT.AddressOf(results,"pin_std"),"pin_std/I")


    tg = ROOT.TGraphErrors()
    tg.SetMarkerStyle(23)
    tg.GetXaxis().SetTitle("IPW")
    tg.GetYaxis().SetTitle("PIN")
    tg.SetTitle("Channel %02d"%channel)

    sc.clear_channel()
    sc.select_channel(channel)
    sc.set_pulse_width(16383)
    sc.set_pulse_delay(1.0)
    sc.set_pulse_number(500)
    sc.set_fibre_delay(0)
    sc.set_trigger_delay(0)
    sc.disable_external_trigger()
    
    ipt = 0

    for height in heights:
        print height
        sc.set_pulse_height(height)
        #sc.fire()
        #time.sleep(0.25)
        for num in pinReads:
            pin = None
            sc.fire()
            time.sleep(0.25)
            while pin==None:
                pin = sc.read_pin()
                tmpList = pin[0].values()
                pinValue = int(''.join(tmpList))
                pinReadArr[num]=pinValue
                #print pinReadArr[num]
            print pin
        
        pinAvg = numpy.mean(pinReadArr)
        pinStd = numpy.std(pinReadArr)
        results.pin_avg = pinAvg
        results.pin_std = pinStd
        results.height = height
        tt.Fill()
        tg.SetPoint(ipt,float(height),float(pinAvg))
        tg.SetPointError(ipt,float(0),float(pinStd))
        print "Height:",height,"PIN",pinAvg,"+/-",pinStd
        ipt += 1
        tg.Draw("ap")
        tc.Update()

#    raw_input("wait")

    tt.Write()
    tf.Close()
        
        
