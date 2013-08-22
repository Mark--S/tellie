#!/usr/bin/env python
################################
# plot_ipw.py
#
# Makes plots for the IPW scan of the chosen 
# channel.  Stores plots in TFile and also 
# creates pdfs.
#
################################

import scan_tools
import ROOT

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

def get_time_

        sigma = 0.6741;
			gain = 15460;
		}
		if (gainVolt > 0.7){
			sigma = 0.6459;
			gain = 192750;
		}
		photons = -(integ/(50.*1.602E-19*gain)); //nb of photons detected
		photons /= QE; // nb of photons struck


def get_photons(volts_seconds,applied_volts):
    """Use the integral (Vs) from the scope to get the number of photons
    """
    gain = get_gain(applied_volts)

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box")
    parser.add_option("-c",dest="channel")
    parser.add_option("-t",dest="type",default="broad")
    (options,args) = parser.parse_args()

    
