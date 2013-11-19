import ROOT
import sys
import math

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

    dev1 = f1.GetParameter(2)
    dev2 = f2.GetParameter(2)

    err = math.sqrt(dev1*dev1+dev2*dev2)

    diff = mean2 - mean1


    canvas = ROOT.TCanvas()
    canvas.cd()
    hist.GetXaxis().SetTitle('PIN Number')
    hist.GetYaxis().SetTitle('Number of readings')
    hist.Draw()

    max_y = hist.GetMaximum()

    line1 = ROOT.TLine()
    line1.DrawLine(mean,0,mean,max_y)

    latex = ROOT.TLatex()
    text = 'Mean: %.2f' % (mean)
    latex.SetTextSize(0.04)
    latex.DrawLatex(mean+20,max_y,text)
    latex1 = ROOT.TLatex()
    latex1.SetTextColor(ROOT.kRed)    
    text = '#splitline{Mean: %.2f}{Sigma: %.2f}' % (mean1,dev1)
    latex1.SetTextSize(0.04)
    latex1.DrawLatex(mean1+diff*0.1,max_y-40,text)
    latex2 = ROOT.TLatex()
    latex2.SetTextColor(ROOT.kBlue)
    text = '#splitline{Mean: %.2f}{Sigma: %.2f}' % (mean2,dev2)   
    latex2.SetTextSize(0.04)
    latex2.DrawLatex(mean-diff*0.2,max_y-20,text)
    canvas.Print(plot_name)

    return err, diff

if __name__ == '__main__':
    file_names = sys.argv[1]
    g1 = ROOT.TGraphErrors()
    ctr = 0
    for line in open(file_names,'r').readlines():
        line = line.strip()
        width = float(line[-9:-4])
        print width
        err, diff = plot_hist(line)
        g1.SetPoint(ctr,width,diff)
        g1.SetPointError(ctr,0,err)
        ctr += 1

    g1.SetMarkerStyle(20)
    g1.GetXaxis().SetTitle('IPW')
    g1.GetYaxis().SetTitle('Difference in PIN Peak Values')
    canvas = ROOT.TCanvas()
    canvas.cd()
    g1.Draw('AP')
    raw_input("any key to quit: ")
    canvas.Print('results.pdf')

