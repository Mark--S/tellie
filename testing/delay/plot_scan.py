import os
import utils
import ROOT

delays = ["NoDelay",0,10,20,30,40,50]
triggers = ["TrigDelay","NoTrigDelay"]

gr_raw = []
gr_fixed = []
can_raw = []
can_fixed = []

legend = []

ctr = 0

colors = [ROOT.kBlack,ROOT.kMagenta,ROOT.kRed+1,ROOT.kOrange,
          ROOT.kYellow+1,ROOT.kGreen+1,ROOT.kCyan+1,ROOT.kBlue+1]

for i_t,trigger in enumerate(triggers):

    canname = "can_raw_%s"%(trigger)
    can_raw.append(ROOT.TCanvas(canname,canname))
    canname = "can_fixed_%s"%(trigger)
    can_fixed.append(ROOT.TCanvas(canname,canname))

    legend.append(ROOT.TLegend(0.1,0.6,0.3,0.9))
    legend[i_t].SetFillColor(0)

    for i_d,delay in enumerate(delays): 
        delay_adj = 0
        fname = "scan/Waveform_Box01_Chan01_%s_%s"%(trigger,delay)
        if type(delay)==int:
            delay_adj = delay
            fname = "scan/Waveform_Box01_Chan01_%s_%02d"%(trigger,delay)
        
        results = utils.PickleFile(fname,2)
        results.load()
        
        signal_t = results.get_meta_data("timeform_2")
        signal_v = results.get_data(1)[0]
        
        gr_raw.append(ROOT.TGraph())
        gr_raw[ctr].SetTitle(trigger)
        gr_raw[ctr].SetName("raw %s %s"%(trigger,delay))
        gr_raw[ctr].SetLineColor(colors[i_d-1])

        gr_fixed.append(ROOT.TGraph())
        gr_fixed[ctr].SetTitle(trigger)
        gr_fixed[ctr].SetName("fixed %s %s"%(trigger,delay))
        gr_fixed[ctr].SetLineColor(colors[i_d-1])
        
        for i in range(len(signal_t)):
            gr_raw[ctr].SetPoint(i,signal_t[i]*1e9,signal_v[i])
            gr_fixed[ctr].SetPoint(i,signal_t[i]*1e9-delay_adj,signal_v[i])

        option = "al"
        if i_d!=0:
            option = "l"

        can_raw[i_t].cd()
        gr_raw[ctr].Draw(option)
        gr_raw[ctr].GetXaxis().SetRangeUser(400,550)
        
        can_fixed[i_t].cd()
        gr_fixed[ctr].Draw(option)
        gr_fixed[ctr].GetXaxis().SetRangeUser(400,550) 
       
        if type(delay)==int:
            legend[i_t].AddEntry(gr_raw[ctr],"%02d ns"%(delay),"l")
        else:
            legend[i_t].AddEntry(gr_raw[ctr],delay,"l")

        ctr+=1

    can_raw[i_t].cd()
    legend[i_t].Draw()
    can_raw[i_t].Update()

    can_fixed[i_t].cd()
    legend[i_t].Draw()
    can_fixed[i_t].Update()

raw_input("wait")
