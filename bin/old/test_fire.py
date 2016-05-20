import os
import time
from core import serial_command

sc = serial_command.SerialCommand()
sc.select_channel(3)
sc.set_pulse_number(1000)
sc.set_pulse_width(0)
sc.set_pulse_height(16383)
sc.set_pulse_delay(001.000)
sc.set_fibre_delay(0)
sc.set_trigger_delay(600)
sc.fire()
time.sleep(5)
pn = sc.read_pin()
print pn
for i in range(5):
    time.sleep(0.1)
    print sc._serial.read(100)
