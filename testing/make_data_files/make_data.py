####################
# make_data.py
#
# Script to create the database files
# that hold the mapping of photons:IPW
# for all TELLIE channels
####################

from common import results
import json

def get_ipw(gr_photons_vs_ipw,n_photons):
    """Get the IPW setting for the given light level
    """  
    x = gr_photons_vs_ipw.GetX()
    y = gr_photons_vs_ipw.GetY()
    n = gr_photons_vs_ipw.GetN()
    if y[0]<n_photons:
        raise Exception,"Couldnt find IPW level for %s (max %.1f, min %.1f)"%(n_photons,y[0],y[n-1])
    for i in range(n):
        if y[i]<n_photons:
            return int(x[i])
    raise Exception,"Couldnt find IPW level for %s (max %.1f, min %.1f)"%(n_photons,y[0],y[n-1])

levels = {1e3:"low",1e4:"low",1e5:"broad"}

ipw = {}

for ibox in range(1,13):
    for ichan in range(1,9):
        channel = (ibox-1)*8 + ichan
        ipw[channel] = {}
        gr_broad = results.get_broad_graph(ibox,channel,"gPhoVsVolt")
        gr_low = results.get_low_graph(ibox,channel,"gPhoVsVolt")
        #now assess ROUGHLY where we can get 100k, 10k and 1k photons from each      
        for l in levels:
            ipw[channel][int(l)]={}
            if levels[l]=="low":
                try:
                    ipw[channel][int(l)]["pulse_width"] = get_ipw(gr_low,l)
                except:
                    print "USING BROAD for %s channel %d"%(l,channel)
                    ipw[channel][int(l)]["pulse_width"] = get_ipw(gr_broad,l)
            else:
                try:
                    ipw[channel][int(l)]["pulse_width"] = get_ipw(gr_broad,l)
                except:
                    print "USING LOW for %s channel %d"%(l,channel)
                    ipw[channel][int(l)]["pulse_width"] = get_ipw(gr_low,l)                
            ipw[channel][int(l)]["pulse_height"] = 16383
            ipw[channel][int(l)]["fibre_delay"] = 0

fout = file("save_file.js","w")
fout.write(json.dumps(ipw,indent=4))
fout.close()
