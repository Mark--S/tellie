import scopes


_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,1000]


def get_volts_div(signal):
    setting = None
    for i,t in enumerate(_v_div):
        if signal > t:
            if i<(len(_v_div)-2):
                setting = _v_div[i+1]
            else:
                setting = _v_div[-2]
    if setting==None:
        setting = _v_div[0] # set to minimal
    return setting
