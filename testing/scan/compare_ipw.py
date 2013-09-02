#!/usr/bin/env python
##########################
#compare_ipw.py
#
#Compare the photon vs pin plots from the 
#Sussex 2013 tests to tests carried out at site
##########################
import ROOT
import os
import sys
import optparse

def get_box_name(box):
    return "Box_%02d"%box
def get_channel_name(channel):
    return "Channel_%03d"%channel
def get_snolab_channel_name(channel):
    return "channel_%02d"%channel

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box")
    parser.add_option("-c",dest="channel")
    parser.add_option("-t",dest="type",default="broad")
    (options,args) = parser.parse_args()

    box = int(options.box)
    channel = int(options.channel)
    logical_channel = (box-1)*8 + channel

    #result name from Sussex
    result_name = None
    if options.type=="broad":
        result_name = "idvLED_IPW_broad"
    elif options.type=="low_intensity":
        result_name = "idvLED_IPW_lowI"
    else:
        print "UNKNOWN RESULT NAME"
        
    sussex_file = ROOT.TFile("~/Dropbox/Test_procedure/Macros/PushPullTests.root","read")
    dirname = "Calib/%s/%s/%s" % (get_box_name(box),get_channel_name(logical_channel),result_name)
    directory = sussex_file.Get(dirname)
    
    filename = "%s/%s/plots/plots.root"%(options.type,get_snolab_channel_name(logical_channel))
    snolab_file = ROOT.TFile(filename,"read")

    sussex_photon_vs_pin = directory.Get("gPhoVsPin")
    snolab_photon_vs_pin = snolab_file.Get("scope_photon_vs_pin")
    snolab_calc_photon_vs_pin = snolab_file.Get("calc_photon_vs_pin")

    sussex_photon_vs_pin.SetMarkerColor(ROOT.kBlue+1)
    sussex_photon_vs_pin.SetMarkerStyle(8)
    snolab_photon_vs_pin.SetMarkerColor(ROOT.kRed+1)
    snolab_photon_vs_pin.SetMarkerStyle(23)
    snolab_calc_photon_vs_pin.SetMarkerColor(ROOT.kGreen+1)
    snolab_calc_photon_vs_pin.SetMarkerStyle(25)
    
    can = ROOT.TCanvas()

    legend = ROOT.TLegend(0.2,0.7,0.4,0.9)
    legend.SetFillColor(0)

    sussex_photon_vs_pin.Draw("ap")
    snolab_photon_vs_pin.Draw("p")
    snolab_calc_photon_vs_pin.Draw("p")

    legend.AddEntry(sussex_photon_vs_pin,"Sussex","p")
    legend.AddEntry(snolab_photon_vs_pin,"SNOLAB-scope","p")
    legend.AddEntry(snolab_calc_photon_vs_pin,"SNOLAB-python","p")
    legend.Draw()

    sussex_photon_vs_pin.GetXaxis().SetTitle("pin")
    sussex_photon_vs_pin.GetYaxis().SetTitle("Photons")   

    can.Print("test.pdf")
    
    ROOT.gStyle.SetOptStat(0)

    lowhist = ROOT.TH2F("lowhist",";pin;Photons",4000,0,4000,5000,0,20000)
    lowhist.Draw()
    sussex_photon_vs_pin.Draw("p")
    snolab_photon_vs_pin.Draw("p")
    snolab_calc_photon_vs_pin.Draw("p")
    legend.Draw()

    can.Print("test2.pdf")
    

    raw_input("any key to continue...")
