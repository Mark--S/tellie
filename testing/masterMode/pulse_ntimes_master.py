###################################################
# Pulses TELLIE in continuous mode.
# This script produces a continuous
# signal to allow for adjustments of
# the PIN diode pots.
# 
# Author: Ed Leming <e.leming09@googlemail.com>
# Date: 01/05/15
###################################################
from core.tellie_server import SerialCommand
import optparse
import sys
import time

def read_pin():
    '''Wait keep looking for pin. It will be retuned when the sequence ends
    '''
    pin, rms = None, None
    try:
        while (pin == None):
            pin, rms, channel = sc.read_pin_sequence()
    except KeyboardInterrupt:
        print "Keyboard interrupt"
    except TypeError:
        pin, rms = read_pin()
    return int(pin), float(rms)

def safe_exit(sc,e):
    print "Exit safely"
    print e
    sc.stop()

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-w",dest="width",default=0,help="IPW setting (0-16383)")
    parser.add_option("-n",dest="npulses",default=10000,help="Number of times for tellie to pulse")
    (options,args) = parser.parse_args()

    width = int(options.width)
    channel = (int(options.box)-1)*8 + int(options.channel)
    width = int(options.width)
    npulses = int(options.npulses)
    sc = SerialCommand("/dev/ttyUSB0")
    sc.stop()
    
    sc.select_channel(channel)
    sc.set_pulse_height(16383)
    sc.set_pulse_width(width)
    delay = 1
    sc.set_pulse_delay(delay)
    sc.set_pulse_number(npulses)
    sc.set_fibre_delay(0)
    sc.set_trigger_delay(0)
    
    time.sleep(0.1)
    sc.fire_sequence()
    tsleep = npulses * (delay*1e-3 + 210e-6)
    time.sleep(tsleep) #add the offset in
    time.sleep(2.5)

    #print "PIN %s RMS %s " %(pinDict[channel][0], pinDict[channel][1])
    pinDict = None
    while pinDict == None:
        pin, rms = read_pin()
    print "PIN %s RMS %s " %(pin, rms)
    sc.stop()
    

