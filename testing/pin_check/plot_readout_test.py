import ROOT
import sys

def plot_hist(result_name):
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

    canvas = ROOT.TCanvas()
    canvas.cd()
    hist.Draw()
    canvas.Print(plot_name)

    raw_input("any key to quit: ")

if __name__ == '__main__':
    print sys.argv[1]
    results_name = sys.argv[1]
    plot_hist(results_name)
