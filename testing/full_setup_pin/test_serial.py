import sys
import time
from core.tellie_server import SerialCommand
from common import parameters as p

sc = SerialCommand(p._serial_port)   # set in tellie.cfg

channels = range(2,17)
try:
    channels = [int(sys.argv[1])]
    print "RUNNING CHANNEL",channels
except:
    pass
print channels
widths = range(0,1000,500)

sc.select_channel(channels[0])
sc.set_pulse_height(p._max_pulse_height)
sc.set_pulse_delay(p._pulse_delay)
sc.set_pulse_number(p._pulse_num)
sc.set_fibre_delay(0)
sc.set_trigger_delay(0)
sc.disable_external_trigger()
sc.set_pulse_width(p._max_pulse_width)
sc.fire()
time.sleep(p._medium_pause)
pin = None
while pin==None:
    pin = sc.read_pin()
print "DARK FIRE OVER: PIN",pin
time.sleep(p._medium_pause)

for channel in channels:

    print "running channel",channel
    
    sc.clear_channel()
    time.sleep(p._short_pause)
    sc.select_channel(channel)
    time.sleep(p._short_pause)
    sc.set_pulse_height(p._max_pulse_height)
    time.sleep(p._short_pause)
    sc.set_pulse_delay(p._pulse_delay)
    time.sleep(p._short_pause)
    sc.set_pulse_number(p._pulse_num)
    time.sleep(p._short_pause)
    sc.set_fibre_delay(0)
    time.sleep(p._short_pause)
    sc.set_trigger_delay(0)
    time.sleep(p._short_pause)

    for width in widths:
        sc.set_pulse_width(width)
        sc.fire()
        time.sleep(p._medium_pause)
        pin = None
        while pin==None:
            pin = sc.read_pin()

        print "WIDTH:",width,"PIN",pin
#    raw_input("wait")

        
