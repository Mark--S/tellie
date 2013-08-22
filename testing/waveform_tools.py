import os
import sys
import math

def get_noise_and_RMS(x_values,y_values):
    ''' Returns the average noise of the PMT and the noise's RMS
    '''
    noise = 0
    noise_sq = 0
    for i in range(len(y_values)):
        # This is arbitary 200 ns region of noise
        if x_values[i]<-100e-9 and x_values[i]>-300e-9:
            noise += y_values[i]
            noise_sq += y_values[i]*y_values[i]

    noise /= n_baseline
    noise_sq /= n_baseline

    rms = math.sqrt(noise_sq - noise*noise)
    return noise, rms

def get_baseline (x_values,y_values):
    ''' Returns the baseline offset on the PMT
    '''
    baseline = 0 
    n_baseline = 0
    for i in range(len(y_values)):
        #This is an arbitary 200 ns region of noise
        if x_values[i]<-100e-9 and x_values[i]>-300e-9:
            baseline += y_values[i]
            n_baseline += 1
    baseline /= n_baseline
    return baseline

def get_photons(integ, volt_gain):
    '''Returns the number of photons given an integral an the voltage applied
    to the PMT
    '''
    #Quantum Efficency of PMT
    QE = 0.192
    if volt_gain < 0.7:
        pmt_gain = 15460
    if volt_gain > 0.7:
        pmt_gain = 192750
    # Photons detected = integral/(resistance*e-Charge*pmt gain)
    photons = -integ/(50.*1.602e-19*pmt_gain)
    # Photons struck = photons detected/quantum efficency
    photons /= QE
    return photons

def get_max_y (x_values,y_values):
    ''' Returns the maximum y value with the baseline adjusted and its index
    '''
    max_y = 0
    baseline = get_baseline(x_values, y_values)
    for i in range(len(y_values)):
        #Adjust baseline
        y_values[i] = y_values[i] - baseline
        if y_values[i]<max_y:
            max_y = y_values[i]
            max_i = i
    return max_y, max_i

def integrate (x_values,y_values, x_low = -5e-9, x_high = 23e-9):
    ''' Integrates waveform. x values are time in s y values in V
    pass a list of x_values and y_values.
    x_low and x_high are the integration window values
    '''
    #Get Baseline offset
    baseline = get_baseline(x_values,y_values)

    # tdiff is the time difference between data points from the scope in seconds
    tdiff = (x_values[3]-x_values[2])

    #INTEGRATE!
    integ = 0
    for i in range(len(y_values)):
        #Integrate between the the time window required
        if x_values[i]>x_low and x_values[i]<=x_high:
            #Adjust baseline
            integ += (y_values[i] + y_values[i+1] - 2*baseline)/2 * tdiff
    return integ

def get_width(x_values, y_values, volt_gain, x_low = -5e-9, x_high = 23e-9,):
    ''' Gets FWHM in ns of the waveform between the time window defined by
    x_low and x_high
    '''
    print x_values
    baseline = get_baseline(x_values,y_values)
    # Get maxmium amplitude and its index
    max_y, max_i = get_max_y(x_values,y_values)
    start_x = 0
    end_x = 0

    #Get half max left
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i < max_i:
                if (y_values[i]- baseline) > max_y*0.5:
                    start_x = x_values[i-1]*1e9
                    break

    #Get half max right
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i > max_i:
                if (y_values[i]-baseline) < max_y*0.5:
                    end_x = x_values[i-1]
                    break
    if volt_gain < 0.7:
        time_correction = 0.6741
    if volt_gain > 0.7:
        time_correction = 0.6459
    #Apply width correction
    try:
        width =  2.355*math.sqrt((((end_x-start_x)*(end_x-start_x))/(2.355*2.355))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the fall time. Returning 0'
        return 0

def get_rise(x_values, y_values, volt_gain, x_low = -5e-9, x_high = 23e-9):
    ''' Gets rise time in ns of the waveform between the time window defined by
    x_low and x_high
    '''
    baseline = get_baseline(x_values,y_values)
    # Get maxmium amplitude and its index
    max_y, max_i = get_max_y(x_values,y_values)
    start_x = 0
    end_x = 0
    # Get 10% max
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i < max_i:
                # Neg y_values
                if (y_values[i] - baseline) < max_y*0.1:
                    print y_values[i] - baseline
                    start_x = x_values[i-1]*1e9
                    break
    # Get 90% max
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i < max_i:
                # Neg y_values
                if (y_values[i] - baseline) < max_y*0.9:
                    end_x = x_values[i-1]*1e9
                    break
    if volt_gain < 0.7:
        time_correction = 0.6741
    if volt_gain > 0.7:
        time_correction = 0.6459
    #Apply rise correction
    try:
        rise =  1.687*math.sqrt((((end_x-start_x)*(end_x-start_x))/(1.687*1.687))-time_correction*time_correction)
        return rise
    except:
        print 'ERROR: Could not calculate the rise time. Returning 0'
        return 0        


def get_fall(x_values, y_values,volt_gain,  x_low = -5e-9, x_high = 23e-9):
    ''' Gets rise time in ns of the waveform between the time window defined by
    x_low and x_high
    '''
    baseline = get_baseline(x_values,y_values)
    # Get maxmium amplitude and its index
    max_y, max_i = get_max_y(x_values,y_values)
    start_x = 0
    end_x = 0

    # Get 90% max
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i > max_i:
                if (y_values[i] - baseline) > max_y*0.9:
                    start_x = x_values[i-1]*1e9
                    break
    # Get 10% max
    for i in range(len(y_values)):
        if x_values[i] > x_low and x_values[i] <= x_high:
            if i > max_i:
                if (y_values[i] - baseline) > max_y*0.1:
                    end_x = x_values[i-1]*1e9
                    break
    if volt_gain < 0.7:
        time_correction = 0.6741
    if volt_gain > 0.7:
        time_correction = 0.6459
    #Apply fall correction
    try:
        fall =  1.687*math.sqrt((((end_x-start_x)*(end_x-start_x))/(1.687*1.687))-time_correction*time_correction)
        return fall


