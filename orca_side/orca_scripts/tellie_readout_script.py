#!/usr/bin/env python
import sys
import argparse
import xmlrpclib
import json as json
from pprint import pprint

if __name__=="__main__":
    try:
        #print "Attempting to connect to tellie hardware"
        parser = argparse.ArgumentParser("Usage: orca_stop_script.py")
        parser.add_argument("-s", dest="server", default="localhost", help="Server address to use [localhost]")
        parser.add_argument("-p", dest="port", default="5030", help="Port number [5030]")
        args = parser.parse_args()

        tellie_server= xmlrpclib.ServerProxy('http://%s:%s' % (args.server, args.port))
    
        # Unsure of how to report different errors to Orca
        # Return values?  Seems ugly.

        try:
            channelDict, channels = tellie_server.read_pin_sequence()
            pins = channelDict[channels][0]
            rms = channelDict[channels][1]
            #print "PIN READOUT:", pins, channels
            if pins is None:
                # Sequence is incomplete; handle in return type?
                sys.exit(1)
            else:
                ############################
                # ALL THIS SEEMS MENTAL??
                ############################
                # This is fine, report the pin in a print
                #DO NOT CHANGE this as Orca uses this to fill the tellie database 
                #json_data=open(pins)
                #data = json.load(json_data)
                #json_data.close()
                pins = str(pins) #cast down to a string
                indexOfStartPoint = pins.find("'")
                reducePins  = pins[indexOfStartPoint+1:-1]
                indexOfEndPoint = indexOfStartPoint + 1 +reducePins.find("'")
                readBackValue = pins[indexOfStartPoint+1:indexOfEndPoint+1]
                #second iterations
                pins = pins[indexOfEndPoint+1:-1]
                #print pins
                indexOfStartPoint = pins.find("'")
                #print indexOfStartPoint
                reducePins  = pins[indexOfStartPoint+1:-1]
                print reducePins
                #indexOfEndPoint = indexOfStartPoint + reducePins.find("'")
                #readBackValue = pins[indexOfStartPoint+2:indexOfEndPoint-1]
                #print readBackValue
                #print "1"
        except xmlrpclib.Fault, e:
            print "Error! attempting to exit safely", e
            tellie_server.stop()
    except:
        print "Unable to make connection to Tellie"
