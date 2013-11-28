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
try:
    import utils
except ImportError:
    pass
try:
    import get_waveform
except ImportError:
    pass
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

def set_style(gr,style):
    if style==1:
        gr.SetMarkerColor(ROOT.kBlue+1)
        gr.SetMarkerStyle(4)
    else:
        gr.SetMarkerColor(ROOT.kRed+1)
        gr.SetMarkerStyle(25)
    
if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-f", dest="file")
    parser.add_option("-s", dest="scope", default="Tektronix")
    (options,args) = parser.parse_args()
    
    if options.scope!="Tektronix" and options.scope!="LeCroy":
        print "Can only run for LeCroy or Tektronix"
        sys.exit()

    sweep_type = options.file.split('/')[0]
    file_name = options.file.split('/')[1]
    box = int(file_name.split('_')[0][-2:])
    channel = int(file_name.split('_')[1][-1:])
    logical_channel = (box-1) * 8 + channel

    voltage = 0
    if sweep_type=="low_intensity":
        voltage = 0.8
    elif sweep_type=="broad":
        voltage = 0.6
    else:
        raise Exception,"unknown sweep type %s"%(sweep_type)

    dirname = os.path.join(sweep_type,"channel_%02d"%logical_channel)

    ipw,pin,width,rise,fall,area = read_scope_scan(options.file)

    #make plots!
    scope_photon_vs_pin = ROOT.TGraph()
    scope_photon_vs_ipw = ROOT.TGraph()
    scope_width_vs_photon = ROOT.TGraph()
    scope_width_vs_ipw = ROOT.TGraph()
    scope_rise_vs_photon = ROOT.TGraph()
    scope_rise_vs_ipw = ROOT.TGraph()
    scope_fall_vs_photon = ROOT.TGraph()
    scope_fall_vs_ipw = ROOT.TGraph()
    
    calc_photon_vs_pin = ROOT.TGraph()
    calc_photon_vs_ipw = ROOT.TGraph()
    calc_width_vs_photon = ROOT.TGraph()
    calc_width_vs_ipw = ROOT.TGraph()
    calc_rise_vs_photon = ROOT.TGraph()
    calc_rise_vs_ipw = ROOT.TGraph()
    calc_fall_vs_photon = ROOT.TGraph()
    calc_fall_vs_ipw = ROOT.TGraph()
 
    pin_vs_ipw = ROOT.TGraph()

    ctr = 0

    wave_can = ROOT.TCanvas("wave_can", "wave_can")

    # Tektronix scope settings:
    x_low = -5e-9
    x_high = 23e-9
    baseline_low = -300e-9 #more waveform on the tek scope
    baseline_high = -100e-9
    if options.scope == "LeCroy":
        baseline_low = 0.0e-9
        baseline_high = 15.0e-9
        x_low = 18.0e-9
        x_high = 45.0e-9

    for i in range(len(ipw)):

        print "IPW: %04d"%(ipw[i])        

        #first, plot the scope values

        photon = get_photons(area[i],voltage)
        rise_time = adjust_rise(rise[i]*1e9,voltage)
        fall_time = adjust_rise(fall[i]*1e9,voltage)
        width_time = adjust_width(width[i]*1e9,voltage)

        pin_vs_ipw.SetPoint(i,ipw[i],pin[i])

        scope_photon_vs_pin.SetPoint(i,pin[i],photon)
        scope_photon_vs_ipw.SetPoint(i,ipw[i],photon)
        scope_rise_vs_photon.SetPoint(i,photon,rise_time)
        scope_rise_vs_ipw.SetPoint(i,ipw[i],rise_time)
        scope_fall_vs_photon.SetPoint(i,photon,fall_time)
        scope_fall_vs_ipw.SetPoint(i,ipw[i],fall_time)
        scope_width_vs_photon.SetPoint(i,photon,width_time)
        scope_width_vs_ipw.SetPoint(i,ipw[i],width_time)

        #now, the values from the graphs directly
        waveform_name = os.path.join(dirname,"Chan%02d_Width%05d"%(logical_channel,ipw[i]))

        # For Tektronix:
        if options.scope=="Tektronix":
            if not os.path.exists("%s.pkl"%waveform_name):
                print "SKIPPING",waveform_name
                continue
            waveform = utils.PickleFile(waveform_name,1)
            waveform.load()
            wave_times = waveform.get_meta_data("timeform_1")
            wave_volts = waveform.get_data(1)[0]
            
            
        else:
            wave_times, wave_volts = get_waveform.get_waveform(waveform_name)
        
        wave_can.cd()
        gr = ROOT.TGraph()
        for j, t in enumerate(wave_times):
            gr.SetPoint(j, t, wave_volts[j])
        gr.Draw("alp")
        wave_can.Update()

        raw_input("wait:")

        baseline = waveform_tools.get_baseline(wave_times, wave_volts, baseline_low, baseline_high)
            
        # Compute the area, rise, fall and width *using the baseline that has already been found from the pre-signal region (scope specific)*
        w_area = waveform_tools.integrate(wave_times, wave_volts, x_low = x_low, x_high = x_high, baseline = baseline)
        w_photon = get_photons(w_area, voltage)
        w_rise = waveform_tools.get_rise(wave_times, wave_volts,voltage, x_low = x_low, x_high = x_high, baseline = baseline)
        w_fall = waveform_tools.get_fall(wave_times,wave_volts,voltage, x_low = x_low, x_high = x_high, baseline = baseline)
        w_width = waveform_tools.get_width(wave_times,wave_volts,voltage, x_low = x_low, x_high = x_high, baseline = baseline)

        calc_photon_vs_pin.SetPoint(ctr,pin[i],w_photon)
        calc_photon_vs_ipw.SetPoint(ctr,ipw[i],w_photon)
        calc_rise_vs_photon.SetPoint(ctr,w_photon,w_rise)
        calc_rise_vs_ipw.SetPoint(ctr,ipw[i],w_rise)
        calc_fall_vs_photon.SetPoint(ctr,w_photon,w_fall)
        calc_fall_vs_ipw.SetPoint(ctr,ipw[i],w_fall)
        calc_width_vs_photon.SetPoint(ctr,w_photon,w_width)
        calc_width_vs_ipw.SetPoint(ctr,ipw[i],w_width)

        ctr+=1

    #Remove any bad scope values
    clean_graph(scope_photon_vs_pin)
    clean_graph(scope_photon_vs_ipw)
    clean_graph(scope_rise_vs_photon)
    clean_graph(scope_rise_vs_ipw)
    clean_graph(scope_fall_vs_photon)
    clean_graph(scope_fall_vs_ipw)
    clean_graph(scope_width_vs_photon)
    clean_graph(scope_width_vs_ipw)

    set_style(pin_vs_ipw,1)

    set_style(scope_photon_vs_pin,1)
    set_style(scope_photon_vs_ipw,1)
    set_style(scope_rise_vs_photon,1)
    set_style(scope_rise_vs_ipw,1)
    set_style(scope_fall_vs_photon,1)
    set_style(scope_fall_vs_ipw,1)
    set_style(scope_width_vs_photon,1)
    set_style(scope_width_vs_ipw,1)

    set_style(calc_photon_vs_pin,2)
    set_style(calc_photon_vs_ipw,2)
    set_style(calc_rise_vs_photon,2)
    set_style(calc_rise_vs_ipw,2)
    set_style(calc_fall_vs_photon,2)
    set_style(calc_fall_vs_ipw,2)
    set_style(calc_width_vs_photon,2)
    set_style(calc_width_vs_ipw,2)

    scope_photon_vs_pin.SetName("scope_photon_vs_pin")
    scope_photon_vs_ipw.SetName("scope_photon_vs_ipw")
    scope_width_vs_photon.SetName("scope_width_vs_photon")
    scope_width_vs_ipw.SetName("scope_width_vs_ipw")
    scope_rise_vs_photon.SetName("scope_rise_vs_photon")
    scope_rise_vs_ipw.SetName("scope_rise_vs_ipw")
    scope_fall_vs_photon.SetName("scope_fall_vs_photon")
    scope_fall_vs_ipw.SetName("scope_fall_vs_ipw")

    calc_photon_vs_pin.SetName("calc_photon_vs_pin")
    calc_photon_vs_ipw.SetName("calc_photon_vs_ipw")
    calc_width_vs_photon.SetName("calc_width_vs_photon")
    calc_width_vs_ipw.SetName("calc_width_vs_ipw")
    calc_rise_vs_photon.SetName("calc_rise_vs_photon")
    calc_rise_vs_ipw.SetName("calc_rise_vs_ipw")
    calc_fall_vs_photon.SetName("calc_fall_vs_photon")
    calc_fall_vs_ipw.SetName("calc_fall_vs_ipw")
    
    output_dir = os.path.join(dirname,"plots")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    can = ROOT.TCanvas()

    pin_vs_ipw.Draw("ap")
    can.Print("%s/pin_vs_ipw.pdf"%output_dir)
    
    scope_photon_vs_pin.Draw("ap")
    calc_photon_vs_pin.Draw("p")
    can.Print("%s/photon_vs_pin.pdf"%output_dir)

    scope_photon_vs_ipw.Draw("ap")
    calc_photon_vs_ipw.Draw("p")
    can.Print("%s/photon_vs_ipw.pdf"%output_dir)

    scope_rise_vs_ipw.Draw("ap")
    calc_rise_vs_ipw.Draw("p")
    can.Print("%s/rise_vs_ipw.pdf"%output_dir)

    scope_rise_vs_photon.Draw("ap")
    calc_rise_vs_photon.Draw("p")
    can.Print("%s/rise_vs_photon.pdf"%output_dir)

    scope_fall_vs_photon.Draw("ap")
    calc_fall_vs_photon.Draw("p")
    can.Print("%s/fall_vs_photon.pdf"%output_dir)

    scope_fall_vs_ipw.Draw("ap")
    calc_fall_vs_ipw.Draw("p")
    can.Print("%s/fall_vs_ipw.pdf"%output_dir)

    scope_width_vs_photon.Draw("ap")
    calc_width_vs_photon.Draw("p")
    can.Print("%s/width_vs_photon.pdf"%output_dir)

    scope_width_vs_ipw.Draw("ap")
    calc_width_vs_ipw.Draw("p")
    can.Print("%s/width_vs_ipw.pdf"%output_dir)

    fout = ROOT.TFile("%s/plots.root"%output_dir,"recreate")
    
    scope_photon_vs_pin.Write()
    scope_photon_vs_ipw.Write()
    scope_width_vs_photon.Write()
    scope_width_vs_ipw.Write()
    scope_rise_vs_photon.Write()
    scope_rise_vs_ipw.Write()
    scope_fall_vs_photon.Write()
    scope_fall_vs_ipw.Write()

    calc_photon_vs_pin.Write()
    calc_photon_vs_ipw.Write()
    calc_width_vs_photon.Write()
    calc_width_vs_ipw.Write()
    calc_rise_vs_photon.Write()
    calc_rise_vs_ipw.Write()
    calc_fall_vs_photon.Write()
    calc_fall_vs_ipw.Write()

    fout.Close()

    raw_input('wait')
