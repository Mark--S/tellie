import ROOT
import sys

def plot_hist(results_name):
    plot_name = results_name.replace(".dat",".pdf")
    
    results = []
    for line in open(results_name,'r').readlines():
        results.append(int(line))

    max_pin = max(results)
    min_pin = min(results)
    diff = int((max_pin-min_pin+1)/20)

    hist = ROOT.TH1F("",";Pin reading",diff,min_pin,max_pin+1)
    for r in results:
        hist.Fill(r)

    mean = hist.GetMean()
    f1 = ROOT.TF1('f1','gaus',0,mean)
    f2 = ROOT.TF1('f2','gaus',mean,100000)
    f1.SetLineColor(ROOT.kRed)
    f2.SetLineColor(ROOT.kBlue)

    hist.Fit(f1,'R')
    hist.Fit(f2,'R+')

    mean1 = f1.GetParameter(1)
    mean2 = f2.GetParameter(1)

    print mean2 - mean1

    canvas = ROOT.TCanvas()
    canvas.cd()
    hist.Draw()
    canvas.Print(plot_name)

    raw_input("any key to quit: ")

if __name__ == '__main__':
    results_name = sys.argv[1]
    plot_hist(results_name)
