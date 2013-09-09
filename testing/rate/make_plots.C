void make_plots(){

    Int_t ipw,pin;
    Float_t delay,delay_actual,area;
    Float_t rate,rate_actual,photons;

    TFile *fin = new TFile("pin_delay_photons_box01_channel01.root","read");
    TTree *tt = (TTree*)fin->Get("tree");
    tt->SetBranchAddress("width",&ipw);
    tt->SetBranchAddress("pin",&pin);
    tt->SetBranchAddress("delay",&delay);
    tt->SetBranchAddress("delay_actual",&delay_actual);
    tt->SetBranchAddress("scope_area",&area);

    Int_t ipw_vals[100] = {0};
    TGraph *grPin[100] = {0};
    TGraph *grArea[100] = {0};
    TGraph *grPinArea[100] = {0};
    int ctr[100]={0};

    TGraph *allPinArea = new TGraph();

    for(int entry=0;entry<tt->GetEntries();entry++){

        tt->GetEntry(entry);
        
        if(!grPin[ipw/100]){
            ipw_vals[ipw/100] = ipw;
            grPin[ipw/100] = new TGraph();
            grArea[ipw/100] = new TGraph();
            grPinArea[ipw/100] = new TGraph();
        }
        float gain = 15460;
        rate = 1./delay;
        rate_actual = 1./delay_actual;
        photons = fabs(area) / (50.0 * 1.6e-19 * gain);
        photons /= 0.192;
        grPin[ipw/100]->SetPoint(ctr[ipw/100],rate_actual,pin);
        grArea[ipw/100]->SetPoint(ctr[ipw/100],rate_actual,photons);
        grPinArea[ipw/100]->SetPoint(ctr[ipw/100],photons,pin);
        allPinArea->SetPoint(entry,photons,pin);
        ctr[ipw/100]++;
    }

    char canname[100];
    for(int i=0;i<100;i++){
        if(grPin[i]){
            sprintf(canname,"can%d",i);
            TCanvas *can = new TCanvas(canname,canname);
            can->cd();
            grPin[i]->SetMarkerStyle(23);
            grPin[i]->GetXaxis()->SetTitle("Rate (Hz)");
            grPin[i]->GetYaxis()->SetTitle("Pin");
            grPin[i]->Draw("ap");
            gPad->SetLogx();
            sprintf(canname,"plots/IPW_%d_PinVsRate.pdf",ipw_vals[i]);
            can->Print(canname);

            sprintf(canname,"can2_%d",i);
            TCanvas *can2 = new TCanvas(canname,canname);
            can2->cd();
            grArea[i]->SetMarkerStyle(23);
            grArea[i]->GetXaxis()->SetTitle("Rate (Hz)");
            grArea[i]->GetYaxis()->SetTitle("Photons");
            grArea[i]->Draw("ap");
            gPad->SetLogx();
            sprintf(canname,"plots/IPW_%d_PhotonVsRate.pdf",ipw_vals[i]);
            can2->Print(canname);

            sprintf(canname,"can3_%d",i);
            TCanvas *can3 = new TCanvas(canname,canname);
            can3->cd();
            grPinArea[i]->SetMarkerStyle(23);
            grPinArea[i]->GetXaxis()->SetTitle("Photons");
            grPinArea[i]->GetYaxis()->SetTitle("Pin");
            grPinArea[i]->Draw("ap");
            sprintf(canname,"plots/IPW_%d_PinVsPhoton.pdf",ipw_vals[i]);
            can3->Print(canname);
        }
    }

    TCanvas *canall = new TCanvas("canall","canall");
    canall->cd();
    allPinArea->SetMarkerStyle(23);
    allPinArea->GetXaxis()->SetTitle("Photons");
    allPinArea->GetYaxis()->SetTitle("Pin");
    allPinArea->Draw("ap");
    sprintf(canname,"plots/all_PinVsPhoton.pdf");
    canall->Print(canname);
    
}
