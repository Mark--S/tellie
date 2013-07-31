import ROOT
import utils
import os
import sys
import numpy
import math

# x values (ns) for the time window
int_low = -5e-9
int_high = 23e-9

#read in the number of photons
fname = #TODO; set the filename
results = utils.PickleFile(fname,1) 
results.load()

data = results.get_data(1)
meta = results.get_meta_data('timeform_1')

tg = ROOT.TGraph()

max_y = 0

noise = 0
noise_sq = 0

baseline = 0
n_baseline = 0
for i in range(len(data[0])):
    if meta[i]<-100e-9 and meta[i]>-300e-9:
        baseline += data[0][i]
        n_baseline += 1
        noise += data[0][i]
        noise_sq += data[0][i]*data[0][i]
baseline /= n_baseline
print baseline

noise /= n_baseline
noise_sq /= n_baseline
rms = math.sqrt(noise_sq - noise*noise)

i_low = -1
i_high = -1

for i in range(len(data[0])):
    if meta[i]<int_low:
        i_low = i
    if meta[i]>int_high and i_high==-1:
        i_high = i
        #convert to ns for integration
        #adjust baseline
    data[0][i] = data[0][i] - baseline
    tg.SetPoint(i,meta[i]*1e9,data[0][i])
    if data[0][i]<max_y:
        max_y = data[0][i]

    
tdiff = (meta[3]-meta[2]) * 1e9
integ = 0
error = 0
n_integ = 0
for i in range(len(data[0])):
    if i>i_low and i<=i_high:
        integ += (data[0][i] + data[0][i+1])/2 * tdiff
        error += rms
        n_integ += 1

print integ
tg.Draw("al")
raw_input("wait")
