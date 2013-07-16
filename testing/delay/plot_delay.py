import ROOT
import utils
import os
import sys
import numpy
import math

if __name__=="__main__":
    fname = sys.argv[1]
    results = utils.PickleFile(fname.split(".")[0],2)
    results.load()
    
    trigger_t = results.get_meta_data("timeform_1")
    signal_t = results.get_meta_data("timeform_2")
    
    #for some reason the channels get switched over!
    trigger_v = results.get_data(2)[0] # only one waveform
    signal_v = results.get_data(1)[0] # only one waveform

    trigger_gr = ROOT.TGraph()
    signal_gr = ROOT.TGraph()

    trigger_gr.SetLineColor(ROOT.kBlack)
    signal_gr.SetLineColor(ROOT.kRed+2)
    
    for i in range(len(trigger_t)):
        trigger_gr.SetPoint(i,trigger_t[i],trigger_v[i]*10) #scale by 10
    for i in range(len(signal_t)):
        signal_gr.SetPoint(i,signal_t[i],signal_v[i])

    trigger_gr.Draw("al")
    signal_gr.Draw("l")
    
    raw_input("wait")
