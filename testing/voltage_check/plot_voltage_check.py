#!/usr/bin/env python
################################
# plot_ipw.py
#
# Makes plots for the IPW scan of the chosen 
# channel.  Stores plots in TFile and also 
# creates pdfs.
#
################################

import waveform_tools
import utils
import ROOT
import math
import optparse
import os

def read_scope_scan(fname):
    """Read data as read out and stored to text file from the scope.
    Columns are: ipw, pin, width, rise, fall, width (again), area.
    Rise and fall are opposite to the meaning we use (-ve pulse)
    """
    fin = file(fname,'r')
    ipw = []
    pin = []
    width = []
    rise = []
    fall = []
    area = []
    for line in fin.readlines():
        if line[0]=="#":
            continue
        bits = line.split()
        if len(bits)!=7:
            continue
        ipw.append(int(bits[0]))
        pin.append(int(bits[1]))
        width.append(float(bits[2]))
        fall.append(float(bits[3])) #rise in file -> fall
        rise.append(float(bits[4])) #fall in file -> rise
        area.append(-float(bits[6])) #-ve pulse
    return ipw,pin,width,rise,fall,area

def get_gain(applied_volts):
    """Get the gain from the applied voltage"""
    gain = None
    if applied_volts < 0.7:
        gain = 15460
    else:
        gain = 192750
    return gain

def get_scope_response(applied_volts):
    """Get the system timing response"""
    scope_response = None
    if applied_volts < 0.7:
        scope_response = 0.6741
    else:
        scope_response = 0.6459
    return scope_response

def adjust_width(seconds,applied_volts):
    """ Adjust the width, removing the scope response time"""
    time_correction = get_scope_response(applied_volts)
    try:
        width =  2.355*math.sqrt(((seconds * seconds)/(2.355*2.355))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the fall time. Returning 0'
        print seconds,time_correction
        return 0

def adjust_rise(seconds,applied_volts):
    """ Adjust EITHER the rise OR fall time (remove scope response)"""
    time_correction = get_scope_response(applied_volts)    
    try:
        width =  1.687*math.sqrt(((seconds * seconds)/(1.687*1.687))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the rise/fall time. Returning 0'
        print seconds,time_correction
        return 0

def get_photons(volts_seconds,applied_volts):
    """Use the integral (Vs) from the scope to get the number of photons.
    Can accept -ve or +ve pulse
    """
    impedence = 50.0 
    eV = 1.602e-19
    qe = 0.192 # @ 488nm
    gain = get_gain(applied_volts)
    photons = math.fabs(volts_seconds) / (impedence * eV * gain)
    photons /= qe
    return photons

def clean_graph(gr):
    """Remove any points on plots that got bad (9e37) scope measurements
    """
    ctr = 0
    for i in range(gr.GetN()-1,-1,-1):        
        if float(repr(gr.GetY()[i]))>1e10:
            print i,repr(gr.GetY()[i])
            gr.RemovePoint(i)

def draw_many(can,gr_arr,xtitle,ytitle,legends,name):
    """Draw many graphs
    """
    legend = ROOT.TLegend(0.2,0.5,0.6,0.9)
    for i in range(len(gr_arr)):
        if i==0:
            gr_arr[i].Draw("ap")
            gr_arr[i].GetXaxis().SetTitle(xtitle)
            gr_arr[i].GetYaxis().SetTitle(ytitle)
        else:
            gr_arr[i].Draw("p")
        legend.AddEntry(gr_arr[i],legends[i],"p")
    leg.Draw()
    can.Update()
    can.Print(name)

def set_style(gr,color,marker):
    gr.SetMarkerColor(color)
    gr.SetMarkerStyle(marker)
    
if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box")
    parser.add_option("-c",dest="channel")
    parser.add_option("-d",dest="type")
    (options,args) = parser.parse_args()
    
    box = int(box)
    channel = int(channel)
    logical_channel = (box-1)*8 + channel  

    scope_photon_vs_pin = []
    scope_photon_vs_ipw = []
    scope_width_vs_photon = []
    scope_width_vs_ipw = []
    scope_rise_vs_photon = []
    scope_rise_vs_ipw = []
    scope_fall_vs_photon = []
    scope_fall_vs_ipw = []
    
    calc_photon_vs_pin = []
    calc_photon_vs_ipw = []
    calc_width_vs_photon = []
    calc_width_vs_ipw = []
    calc_rise_vs_photon = []
    calc_rise_vs_ipw = []
    calc_fall_vs_photon = []
    calc_fall_vs_ipw = []

    ngr = 0

    supply_volt = []
    colors = [ROOT.kBlack,ROOT.kRed+1,ROOT.kBlue+1,ROOT.kGreen+1,ROOT.kCyan+1]
    markers = [8,21,22,23,29]

    for f in os.listdir(options.type):
        fstart = "Box%02d_Channel%d"
        if not f.startswith(fstart):
            continue
        supply_volt.append(float(f.split('_')[2][:-4]))

        pmt_volt = 0
        if sweep_type=="low_intensity":
            pmt_volt = 0.8
        elif sweep_type=="broad":
            pmt_volt = 0.6
        else:
            raise Exception,"unknown sweep type %s"%(sweep_type)

        dirname = os.path.join(options.type,"voltage_%.3f"%supply_volt[ngr],"channel_%02d"%logical_channel)
        
        ipw,pin,width,rise,fall,area = read_scope_scan(options.file)
        
        #make plots!
        scope_photon_vs_pin.append(ROOT.TGraph())
        scope_photon_vs_ipw.append(ROOT.TGraph())
        scope_width_vs_photon.append(ROOT.TGraph())
        scope_width_vs_ipw.append(ROOT.TGraph())
        scope_rise_vs_photon.append(ROOT.TGraph())
        scope_rise_vs_ipw.append(ROOT.TGraph())
        scope_fall_vs_photon.append(ROOT.TGraph())
        scope_fall_vs_ipw.append(ROOT.TGraph())
        
        calc_photon_vs_pin.append(ROOT.TGraph())
        calc_photon_vs_ipw.append(ROOT.TGraph())
        calc_width_vs_photon.append(ROOT.TGraph())
        calc_width_vs_ipw.append(ROOT.TGraph())
        calc_rise_vs_photon.append(ROOT.TGraph())
        calc_rise_vs_ipw.append(ROOT.TGraph())
        calc_fall_vs_photon.append(ROOT.TGraph())
        calc_fall_vs_ipw.append(ROOT.TGraph())
 
        ctr = 0
        
        for i in range(len(ipw)):

            print "IPW: %04d"%(ipw[i])

            #first, plot the scope values
            photon = get_photons(area[i],voltage)
            rise_time = adjust_rise(rise[i]*1e9,voltage)
            fall_time = adjust_rise(fall[i]*1e9,voltage)
            width_time = adjust_width(width[i]*1e9,voltage)

            scope_photon_vs_pin[ngr].SetPoint(i,pin[i],photon)
            scope_photon_vs_ipw[ngr].SetPoint(i,ipw[i],photon)
            scope_rise_vs_photon[ngr].SetPoint(i,photon,rise_time)
            scope_rise_vs_ipw[ngr].SetPoint(i,ipw[i],rise_time)
            scope_fall_vs_photon[ngr].SetPoint(i,photon,fall_time)
            scope_fall_vs_ipw[ngr].SetPoint(i,ipw[i],fall_time)
            scope_width_vs_photon[ngr].SetPoint(i,photon,width_time)
            scope_width_vs_ipw[ngr].SetPoint(i,ipw[i],width_time)

            #now, the values from the graphs directly
            waveform_name = os.path.join(dirname,"Chan%02d_Width%05d"%(logical_channel,ipw[i]))
            if not os.path.exists("%s.pkl"%waveform_name):
                print "SKIPPING",waveform_name
                continue
            waveform = utils.PickleFile(waveform_name,1)
            waveform.load()
            wave_times = waveform.get_meta_data("timeform_1")
            wave_volts = waveform.get_data(1)[0]
            w_area = waveform_tools.integrate(wave_times,wave_volts)
            w_photon = get_photons(w_area,voltage)
            w_rise = waveform_tools.get_rise(wave_times,wave_volts,voltage)
            w_fall = waveform_tools.get_fall(wave_times,wave_volts,voltage)
            w_width = waveform_tools.get_width(wave_times,wave_volts,voltage)
            
            calc_photon_vs_pin[ngr].SetPoint(ctr,pin[i],w_photon)
            calc_photon_vs_ipw[ngr].SetPoint(ctr,ipw[i],w_photon)
            calc_rise_vs_photon[ngr].SetPoint(ctr,w_photon,w_rise)
            calc_rise_vs_ipw[ngr].SetPoint(ctr,ipw[i],w_rise)
            calc_fall_vs_photon[ngr].SetPoint(ctr,w_photon,w_fall)
            calc_fall_vs_ipw[ngr].SetPoint(ctr,ipw[i],w_fall)
            calc_width_vs_photon[ngr].SetPoint(ctr,w_photon,w_width)
            calc_width_vs_ipw[ngr].SetPoint(ctr,ipw[i],w_width)

            ctr+=1

        #Remove any bad scope values
        clean_graph(scope_photon_vs_pin[ngr])
        clean_graph(scope_photon_vs_ipw[ngr])
        clean_graph(scope_rise_vs_photon[ngr])
        clean_graph(scope_rise_vs_ipw[ngr])
        clean_graph(scope_fall_vs_photon[ngr])
        clean_graph(scope_fall_vs_ipw[ngr])
        clean_graph(scope_width_vs_photon[ngr])
        clean_graph(scope_width_vs_ipw[ngr])

        set_style(scope_photon_vs_pin[ngr],colors[ngr],markers[ngr])
        set_style(scope_photon_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(scope_rise_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(scope_rise_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(scope_fall_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(scope_fall_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(scope_width_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(scope_width_vs_ipw[ngr],colors[ngr],markers[ngr])
        
        set_style(calc_photon_vs_pin[ngr],colors[ngr],markers[ngr])
        set_style(calc_photon_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(calc_rise_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(calc_rise_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(calc_fall_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(calc_fall_vs_ipw[ngr],colors[ngr],markers[ngr])
        set_style(calc_width_vs_photon[ngr],colors[ngr],markers[ngr])
        set_style(calc_width_vs_ipw[ngr],colors[ngr],markers[ngr])        

        scope_photon_vs_pin[ngr].SetName("v%.3f_scope_photon_vs_pin"%(supply_volt[ngr]))
        scope_photon_vs_ipw[ngr].SetName("v%.3f_scope_photon_vs_ipw"%(supply_volt[ngr]))
        scope_width_vs_photon[ngr].SetName("v%.3f_scope_width_vs_photon"%(supply_volt[ngr]))
        scope_width_vs_ipw[ngr].SetName("v%.3f_scope_width_vs_ipw"%(supply_volt[ngr]))
        scope_rise_vs_photon[ngr].SetName("v%.3f_scope_rise_vs_photon"%(supply_volt[ngr]))
        scope_rise_vs_ipw[ngr].SetName("v%.3f_scope_rise_vs_ipw"%(supply_volt[ngr]))
        scope_fall_vs_photon[ngr].SetName("v%.3f_scope_fall_vs_photon"%(supply_volt[ngr]))
        scope_fall_vs_ipw[ngr].SetName("v%.3f_scope_fall_vs_ipw"%(supply_volt[ngr]))
        
        calc_photon_vs_pin[ngr].SetName("v%.3f_calc_photon_vs_pin"%(supply_volt[ngr]))
        calc_photon_vs_ipw[ngr].SetName("v%.3f_calc_photon_vs_ipw"%(supply_volt[ngr]))
        calc_width_vs_photon[ngr].SetName("v%.3f_calc_width_vs_photon"%(supply_volt[ngr]))
        calc_width_vs_ipw[ngr].SetName("v%.3f_calc_width_vs_ipw"%(supply_volt[ngr]))
        calc_rise_vs_photon[ngr].SetName("v%.3f_calc_rise_vs_photon"%(supply_volt[ngr]))
        calc_rise_vs_ipw[ngr].SetName("v%.3f_calc_rise_vs_ipw"%(supply_volt[ngr]))
        calc_fall_vs_photon[ngr].SetName("v%.3f_calc_fall_vs_photon"%(supply_volt[ngr]))
        calc_fall_vs_ipw[ngr].SetName("v%.3f_calc_fall_vs_ipw"%(supply_volt[ngr]))

        ngr += 1    

    can = ROOT.TCanvas()

    legends = []
    for i in range(len(scope_photon_vs_pin)):
        legends.append("%.2f V",supply_volt[i])

    outputdir = os.path.join(options.type,"plots","channel_%02d"%logical_channel)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    draw_many(can,scope_photon_vs_pin,"PIN","Photons",legends,"%s/scope_photon_vs_pin.pdf"%(outputdir))
    draw_many(can,scope_photon_vs_ipw,"IPW","Photons",legends,"%s/scope_photon_vs_ipw.pdf"%(outputdir))
    draw_many(can,scope_rise_vs_photon,"Photons","Rise (ns)",legends,"%s/scope_rise_vs_photons.pdf"%(outputdir))
    draw_many(can,scope_rise_vs_ipw,"IPW","Rise (ns)",legends,"%s/scope_rise_vs_ipw.pdf"%(outputdir))
    draw_many(can,scope_fall_vs_photon,"Photons","Fall (ns)",legends,"%s/scope_fall_vs_photons.pdf"%(outputdir))
    draw_many(can,scope_width_vs_ipw,"IPW","Fall (ns)",legends,"%s/scope_width_vs_ipw.pdf"%(outputdir))
    draw_many(can,scope_width_vs_photon,"Photons","Width (ns)",legends,"%s/scope_width_vs_photons.pdf"%(outputdir))
    draw_many(can,scope_width_vs_ipw,"IPW","Width (ns)",legends,"%s/scope_width_vs_ipw.pdf"%(outputdir))

    draw_many(can,calc_photon_vs_pin,"PIN","Photons",legends,"%s/calc_photon_vs_pin.pdf"%(outputdir))
    draw_many(can,calc_photon_vs_ipw,"IPW","Photons",legends,"%s/calc_photon_vs_ipw.pdf"%(outputdir))
    draw_many(can,calc_rise_vs_photon,"Photons","Rise (ns)",legends,"%s/calc_rise_vs_photons.pdf"%(outputdir))
    draw_many(can,calc_rise_vs_ipw,"IPW","Rise (ns)",legends,"%s/calc_rise_vs_ipw.pdf"%(outputdir))
    draw_many(can,calc_fall_vs_photon,"Photons","Fall (ns)",legends,"%s/calc_fall_vs_photons.pdf"%(outputdir))
    draw_many(can,calc_width_vs_ipw,"IPW","Fall (ns)",legends,"%s/calc_width_vs_ipw.pdf"%(outputdir))
    draw_many(can,calc_width_vs_photon,"Photons","Width (ns)",legends,"%s/calc_width_vs_photons.pdf"%(outputdir))
    draw_many(can,calc_width_vs_ipw,"IPW","Width (ns)",legends,"%s/calc_width_vs_ipw.pdf"%(outputdir))
    
    fout = ROOT.TFile("%s/plots.root"%(outputdir),"recreate")
    for i in range(len(scope_photons_vs_pin)):
        scope_photon_vs_pin[i].Write()
        scope_photon_vs_ipw[i].Write()
        scope_rise_vs_photon[i].Write()
        scope_rise_vs_ipw[i].Write()
        scope_fall_vs_photon[i].Write()
        scope_fall_vs_ipw[i].Write()
        scope_width_vs_photon[i].Write()
        scope_width_vs_ipw[i].Write()
        calc_photon_vs_pin[i].Write()
        calc_photon_vs_ipw[i].Write()
        calc_rise_vs_photon[i].Write()
        calc_rise_vs_ipw[i].Write()
        calc_fall_vs_photon[i].Write()
        calc_fall_vs_ipw[i].Write()
        calc_width_vs_photon[i].Write()
        calc_width_vs_ipw[i].Write()
    fout.Close()
