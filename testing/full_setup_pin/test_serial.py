import time
from core import serial_command
import sys

sc = serial_command.SerialCommand()
#sc = serial_command.SerialCommand('/dev/ttyUSB0')

channels = range(2,17)
try:
    channels = [int(sys.argv[1])]
    print "RUNNING CHANNEL",channels
except:
    pass
print channels
widths = range(0,1000,500)

sc.select_channel(channels[0])
sc.set_pulse_height(16383)
sc.set_pulse_delay(1.0)
sc.set_pulse_number(1000)
sc.set_fibre_delay(0)
sc.set_trigger_delay(0)
sc.disable_external_trigger()
sc.set_pulse_width(16383)
sc.fire()
time.sleep(1)
pin = None
while pin==None:
    pin = sc.read_pin()
print "DARK FIRE OVER: PIN",pin
time.sleep(1)

for channel in channels:

    print "running channel",channel
    
    sc.clear_channel()
    time.sleep(0.1)
    sc.select_channel(channel)
    time.sleep(0.1)
    sc.set_pulse_height(16383)
    time.sleep(0.1)
    sc.set_pulse_delay(1.0)
    time.sleep(0.1)
    sc.set_pulse_number(1000)
    time.sleep(0.1)
    sc.set_fibre_delay(0)
    time.sleep(0.1)
    sc.set_trigger_delay(0)
    time.sleep(0.1)

    for width in widths:
        sc.set_pulse_width(width)
        sc.fire()
        time.sleep(2.0)
        pin = None
        while pin==None:
            pin = sc.read_pin()

        print "WIDTH:",width,"PIN",pin
#    raw_input("wait")

        
