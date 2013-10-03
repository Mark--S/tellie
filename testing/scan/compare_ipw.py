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
    parser.add_option("-x",dest="x_axis",default="pin")
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

    x_axis = None
    x_axis_sussex = None
    if options.x_axis=="ipw":
        x_axis = "ipw"
        x_axis_sussex = "Volt"
    elif options.x_axis=="pin":
        x_axis = "pin"
        x_axis_sussex = "Pin"
    else:
        print "UNKNOWN X AXIS"
        
    sussex_file = ROOT.TFile("~/Dropbox/Test_procedure/Macros/PushPullTests.root","read")
    dirname = "Calib/%s/%s/%s" % (get_box_name(box),get_channel_name(logical_channel),result_name)
    directory = sussex_file.Get(dirname)
    
    filename = "%s/%s/plots/plots.root"%(options.type,get_snolab_channel_name(logical_channel))
    snolab_file = ROOT.TFile(filename,"read")
    
    sussex_photon_vs_pin = directory.Get("gPhoVs%s"%(x_axis_sussex))
    snolab_photon_vs_pin = snolab_file.Get("scope_photon_vs_%s"%(x_axis))
    snolab_calc_photon_vs_pin = snolab_file.Get("calc_photon_vs_%s"%(x_axis))

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

    sussex_photon_vs_pin.GetXaxis().SetTitle(x_axis)
    sussex_photon_vs_pin.GetYaxis().SetTitle("Photons")   

    can.Print("%s_%s_%s.pdf"%(get_box_name(box),get_channel_name(channel),x_axis))
    
    ROOT.gStyle.SetOptStat(0)

    lowhist = None
    if x_axis == "ipw":
        lowhist = ROOT.TH2F("lowhist",";%s;Photons"%(x_axis),4000,4000,8000,10000,0,100000)
    else:
        lowhist = ROOT.TH2F("lowhist",";%s;Photons"%(x_axis),4000,0,4000,5000,0,20000)
    lowhist.Draw()
    sussex_photon_vs_pin.Draw("p")
    snolab_photon_vs_pin.Draw("p")
    snolab_calc_photon_vs_pin.Draw("p")
    legend.Draw()

    can.Print("%s_%s_%s_zoom.pdf"%(get_box_name(box),get_channel_name(channel),x_axis))

    raw_input("any key to continue...")
