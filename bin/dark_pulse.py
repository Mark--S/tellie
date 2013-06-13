#!/usr/bin/env python
#####################
#Send dark pulses
#####################

import os
import time
import optparse
import re
from core import serial_command, tellie_exception
from common import tellie_logger

dark_num = 10000
dark_width = 16363

light_num = 100
light_width = 12000

light_shots = 10

#settings used for all
rate = 1000.0 #kHz
height = 16363
channel = 24

pattern = re.compile(r"""\d+""")

def send_command(self,tellie_serial,command):
    if type(command) is str:
        command = [command]
    if type(command) is not list:
        raise tellie_exception.TellieException("Command is not a list: %s %s"%(command,type(command)))
    try:            
        for c in command:
            tellie_serial._serial.write(c) 

def method1(tellie_serial):
    start = time.time()
    print time.time()-start,"START"
    tellie_serial.set_pulse_width(dark_width)
    tellie_serial.set_pulse_number(dark_num)
    tellie_serial.fire()
    time.sleep(1)
    dark_pin = tellie_serial.stop()
    time.sleep(0.1)
    print time.time()-start,"STOP DARK",dark_pin
    tellie_serial.set_pulse_width(light_width)
    tellie_serial.set_pulse_number(light_num)
    tellie_serial.fire()
    light_pin = None
    ctr = 0
    while light_pin==None:        
        light_pin = tellie_serial.read_buffer()
        ctr += 1
        if ctr>10:
            final_check = tellie_serial.stop()
            print "FINAL:",final_check
            raise Exception,"TRIED read %s"%ctr
        print time.time()-start,"LIGHT PIN:",light_pin
        light_pin=None
    
def method2(tellie_serial):

    #first, read the pin from the last shot
    start = time.time()
    print time.time()-start,"START"
    #Check if there is ANYTHING in the buffer
    out = tellie_serial.read_buffer()
    if out!='':
        print "BUFFER NOT EMPTY",out

    #first, set the dark pulses going...
    dark_cmd,_ = serial_command.command_pulse_width(dark_width)
    send_command(tellie_serial,dark_cmd)
    time.sleep(0.1) # Check whether these sleeps are required ...  ARGH!
    dark_cmd,_ = serial_command.command_pulse_number(dark_num)
    send_command(tellie_serial,dark_cmd)
    time.sleep(0.1) # Check whether these sleeps are required ...  ARGH!
    send_command(tellie_serial,serial_command._cmd_fire_series)
    print time.time()-start,"FIRING DARK:"

    #sleep for half a second
    #then check the pin readings to look for last time's reading
    time.sleep(0.5)
    out = tellie_serial.read_buffer()
    pin = pattern.findall(out)
    if len(pin)==2:
        #have readings from last time
        dark_pin = pin[0]
        light_pin = pin[1]
        print "SUCCESS!",out
        print "DARK PIN ",dark_pin
        print "LIGHT PIN",light_pin
    elif len(pin)==0:
        #no readings, probably didn't fire
        print "NO READINGS?",out,pin
        pass
    else:
        print "OH!",out,pin

    #sleep another 0.5
    time.sleep(0.5)
    print time.time()-start,"DONE SLEEP"

    #finally, stop and then send the light commands
    send_command(tellie_serial,serial_command._cmd_stop)
    time.sleep(0.1) # Check whether these sleeps are required ...  ARGH!
    light_cmd,_ = serial_command.command_pulse_width(light_width)
    send_command(tellie_serial,light_cmd)
    time.sleep(0.1) # Check whether these sleeps are required ...  ARGH!
    light_cmd,_ = serial_command.command_pulse_number(light_num)
    send_command(tellie_serial,light_cmd)
    time.sleep(0.1) # Check whether these sleeps are required ...  ARGH!
    send_command(tellie_serial,serial_command._cmd_fire_series)
    #one pulse, then stop? sleep 0.1 s just to be sure
    time.sleep(0.    
    print time.time()-start,"SEQUENCE COMPLETE"

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d",dest="debug",action="store_true",default=False,help="Debug mode")
    (options, args) = parser.parse_args()
    tellie_serial = serial_command.SerialCommand()
    # create a logging object
    logger = tellie_logger.TellieLogger.get_instance()
    logger.set_debug_mode(options.debug)
    # select the dark pulse rates
    delay = 1./rate
    # setup the board settings used for all pulsing
    print "ANYTHING?",tellie_serial.read_buffer()

    tellie_serial.select_channel(channel)
    tellie_serial.set_pulse_height(height)
    tellie_serial.set_pulse_delay(delay)
    
    try:
        start = time.time()
        for i in range(light_shots):
            #method1(tellie_serial)
            method2(tellie_serial)

    except KeyboardInterrupt:
        print 'quitting server'
        tellie_serial.stop()
        print tellie_serial.read_buffer()
    except Exception,e:
        print "Quitting - not an interrupt"
        print e
        tellie_serial.stop()
    except:
        print "WHAT THE FUCK!?"
        tellie_serial.stop()
        
