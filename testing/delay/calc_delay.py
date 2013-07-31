import os
import utils

boxes = range(1,13)
channels = range(1,9)

threshold = -0.1 # should catch the very start of the pulse

for box in boxes:
    for chan in channels:
        fname = "results/Waveform_Box%02d_Chan%02d" % (box,chan)
        if not os.path.exists("%s.pkl"%fname):
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
                idiff = i
                tdiff = signal_t[i]
                break
        if tdiff==None:
            raise Exception,"No signal detected!"
        print "BOX %2d  CHAN %2d : %.1f ns" %(box,chan,(tdiff*1e9)) #to ns from s

