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
    trigger_v = []
    signal_v = []
    trigger_gr = []
    signal_gr = []
    for i in range(5):
        trigger_v.append(results.get_data(2)[i])
        signal_v.append(results.get_data(1)[i])
        trigger_gr.append(ROOT.TGraph())
        signal_gr.append(ROOT.TGraph())        

    for i in range(5):
        trigger_gr[i].SetLineColor(ROOT.kBlack)
        signal_gr[i].SetLineColor(ROOT.kRed+2)
    
        for j in range(len(trigger_t)):
            trigger_gr[i].SetPoint(j,trigger_t[j],trigger_v[i][j])
        for j in range(len(signal_t)):
            signal_gr[i].SetPoint(j,signal_t[j],signal_v[i][j])

        if i==0:
            trigger_gr[i].Draw("al")
        else:
            trigger_gr[i].Draw("l")
        signal_gr[i].Draw("l")
    
    raw_input("wait")
