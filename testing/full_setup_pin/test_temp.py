import time
import ROOT
from core import serial_command

sc = serial_command.SerialCommand()

boxes = range(12)

for ibox in boxes:    

    box = ibox+1    
    #5 probes on each box
    for iprobe in range(5):

        probe = None
        if box<7:
            probe = ibox*5 + iprobe + 1
        else:
            probe = 32 + (ibox-7)*5 + iprobe + 1
        sc.select_temp_probe(probe)
        temp1 = sc.read_temp()
        temp2 = sc.read_temp()
        temp3 = sc.read_temp()
        print probe,':'
        print '\t',temp1
        print '\t',temp2
        print '\t',temp3
        
