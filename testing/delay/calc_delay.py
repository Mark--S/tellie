import os
import utils
import ROOT
from scipy.interpolate import interp1d


boxes = range(1,13)
channels = range(1,9)

threshold = -0.1 # should catch the very start of the pulse

delays = []
channel_list = []

gDelay = ROOT.TGraph()

for box in boxes:
    for chan in channels:

        if box==12 and chan==8:
            continue

        fname = "results/Waveform_Box%02d_Chan%02d" % (box,chan)
        if not os.path.exists("%s.pkl"%fname):
            print "MISSING",fname
            continue
        results = utils.PickleFile(fname,2)
        results.load()
        
        trigger_t = results.get_meta_data("timeform_1")
        signal_t = results.get_meta_data("timeform_2")
    
        #for some reason the channels get switched over!
        trigger_v = results.get_data(2)[0] # only one waveform
        signal_v = results.get_data(1)[0] # only one waveform

        #should be on same time base
        tdiff = None
        for i in range(len(signal_t)):
            if signal_v[i]<threshold:
                #threshold
                interp = interp1d(signal_t[i-5:i+5],signal_v[i-5:i+5], kind = 'cubic')
                break
        t_list = range(signal_t[i-1],signal_t[i+2],0.01)
        for i in range(len(t_list)):
            if interp(t_list[i])<threshold:
                tdiff = t_list[i]
                break
        if tdiff==None:
            raise Exception,"No signal detected!"
        delays.append((tdiff*1e9))
        act_chan = (box-1)*8 + chan
        channel_list.append(float(act_chan))
        print "BOX %2d  CHAN %2d : %.1f ns" %(box,chan,(tdiff*1e9)) #to ns from s
        gDelay.SetPoint(act_chan,float(act_chan),tdiff*1e9)

output = ROOT.TFile("delays.root","RECREATE")
gDelay.SetName('gDelay')
gDelay.Write()
output.Close()
