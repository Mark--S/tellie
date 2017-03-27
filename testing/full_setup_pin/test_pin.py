import sys
import time
import ROOT
from core.tellie_server import SerialCommand
from common import parameters as p

sc = SerialCommand(p._serial_port)   # set in tellie.cfg

channels = [5]
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
widths = range(0,9700,50)

#######################################
#for the branches
ROOT.gROOT.ProcessLine(\
    "struct Results{\
        Int_t width;\
        Int_t pin;\
     };")
from ROOT import Results
results = Results()
########################################

tc = ROOT.TCanvas("can","can")


sc.select_channel(channels[0])
sc.set_pulse_height(p._max_pulse_height)
sc.set_pulse_delay(p._pulse_delay)
sc.set_pulse_number(p._pulse_num)
sc.set_fibre_delay(0)
sc.set_trigger_delay(0)
sc.disable_external_trigger()
sc.set_pulse_width(p._max_pulse_width)
sc.fire()
time.sleep(p._medium_pause)
pin = None
while pin==None:
    pin = sc.read_pin()
print "DARK FIRE OVER: PIN",pin
time.sleep(p._medium_pause)

for channel in channels:

    print "running channel",channel
    
    t_str = time.strftime('%y%m%d_%H.%M')
    fname = "results/pin_width_ch%02d_%s.root"%(channel,t_str)
    tf = ROOT.TFile(fname,"recreate")

    tt = ROOT.TTree("T","T")
    tt.Branch("width",ROOT.AddressOf(results,"width"),"width/I")
    tt.Branch("pin",ROOT.AddressOf(results,"pin"),"pin/I")

    output = open("PIN_IPW_CH%02d.dat"%channel,'a')
    
    tg = ROOT.TGraph()
    tg.SetMarkerStyle(23)
    tg.GetXaxis().SetTitle("IPW")
    tg.GetYaxis().SetTitle("PIN")
    tg.SetTitle("Channel %02d"%channel)

    sc.clear_channel()
    sc.select_channel(channel)
    sc.set_pulse_height(p._max_pulse_height)
    sc.set_pulse_delay(p._pulse_delay)
    sc.set_pulse_number(p._pulse_num)
    sc.set_fibre_delay(0)
    sc.set_trigger_delay(0)
    sc.disable_external_trigger()
    
    ipt = 0

    for width in widths:
        sc.set_pulse_width(width)
        sc.fire()
        time.sleep(p._medium_pause)
        pin = None
        while pin==None:
            pin = sc.read_pin()
#            print pin, channel, pin[0][channel]
        results.pin = int(pin[0][channel])
        results.width = width
        ipin = int(pin[0][channel])
        iwidth = width
        output.write("%d %d\n"%(iwidth,ipin)) 
        tt.Fill()
        tg.SetPoint(ipt,float(iwidth),float(ipin))
        print "WIDTH:",width,"PIN",pin
        ipt += 1
        tg.Draw("ap")
        tc.Update()
    
#    raw_input("wait")
    tc.Print("PINCalib%02d.pdf"%channel)

    tt.Write()
    tf.Close()
        
        
