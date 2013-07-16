#######################################################################
# Gwen Lefeuvre - September 2012
# g.lefeuvre@sussex.ac.uk
#
# TELLIE specific functions, v6
#
#
#######################################################################

import re
import sys
import time
import serial
import json



# unit of waiting times are second
wait     = 0.1   # standard wait for command to be received and executed
longwait = 1     # some requests need longer, eg T readout


# maximal values for the parameters to be passed to TELLIE
MAXLO       = 255.
MAXNBPULSES = 65025		
MAXWH       = 16383		#pulse width and pulse height
MAXPDELAY   = 256.020 	#ms, max delay between pulses
MINPDELAY   = 0.1       #ms, min delay between pulses (ie 10kHz)
MAXTDELAY   = 1275    	#ns, trigger delay, control box
MAXFDELAY   = 127.5   	#ns, fibre length delay, channel






#######################################################################
#
# read the JSON file
#

def ReadRATDB(filename):
	dataDict = json.load(open(filename))
	return dataDict
	



#######################################################################
#
# Operations on serial port
#

serialPortName = '/dev/tty.usbserial-FTE3C0PG'
#serialPortName = '/dev/tty.usbserial-FTF5YKDL'
serialNotOpen  = 'Serial port %s is not open. Exit.' % serialPortName


def openSerial():
	try:
		s = serial.Serial(serialPortName , 9600, timeout=0.5)
	except:
		print serialNotOpen
		sys.exit(1)
	print 'Serial port %s is open.' % serialPortName
	return s


def closeSerial():
	s.close()
	print 'Serial port %s is closed.' % s.portstr
	return
	

def testSerial():
	print 'Serial port is open (true/false): ' % s.isOpen()
	return


def resetSerial():
	t = serial.Serial(serialPortName, 1200, timeout=0.5)
	t.write('@')
	time.sleep( longwait )
	t.close()
	s = openSerial()
	return s




#######################################################################
#
# Settings for each individual channel
#

# clear
#
def clearChannel():
	s.write('C')
	return
		

# led numbering from left to right, 1 to 8
# returns 'B1N' or 'B2N', number is box id
def selectLED(led):
	print 'TELLIE - LED selected : ', led
	s.write('C')
	s.write('I'+chr(led)+'N')
	time.sleep( wait )
	return


# set to max for max intensity
# hi: 0-63, lo: 0-255
# return 'LMP'
def setPulseHeight(par):
	print 'TELLIE - Pulse Height = ', par
	if par <= MAXWH:
		hi = par >> 8
		lo = par & 255
	else:
		print 'WARNING: pulse height above limit, set to maximum: ', MAXWH
		hi = 63
		lo = 255
		
	s.write('L'+chr(hi))
	s.write('M'+chr(lo))
	s.write('P')
	time.sleep( wait )
	return


# set to min to have brightest pulse
# hi: 0-63, lo: 0-255
# returns 'QRS'
def setPulseWidth(par):
	print 'TELLIE - Pulse Width = ', par
	if par <= MAXWH:
		hi = par >> 8
		lo = par & 255

	else:
		print 'WARNING: pulse width above limit, set to maximum: ', MAXWH
		hi = 63
		lo = 255
		
 	s.write('Q'+chr(hi))
 	s.write('R'+chr(lo))
 	s.write('S')
 	time.sleep( wait )
 	return
 

# hi: 0-255, lo: 0-255 
# returns 'HG'
def setPulseNumber(par):
	print 'TELLIE - Pulse Number = ', par
	hi = int(par/255.)
	lo = int((par/255. - hi)*255)

	s.write('H'+chr(hi))
	s.write('G'+chr(lo))
	time.sleep( wait )
	return


# individual channel delay, on each pulse board
# among expert mode functions


# delay between pulses in ms
# ms 0-255 (ms step), us 0-255 (4 us steps, max 1020 us)
# returns 'u'
def setPulseDelay(delay):
	print 'TELLIE - Pulse Delay = ', delay
	if delay > MAXPDELAY:
		delay = MAXPDELAY
	if delay == 0:
		delay = 0.1
	ms = int(delay)
	us = int((delay - ms)*250)
	
	s.write('u'+chr(ms)+chr(us))
	time.sleep( wait )
	return



#######################################################################
#
# Expert mode, high level functions
#

# adjust trigger delay = on the control box
# 0-255, 5ns step, max 1275ns
# returns 'd'
def setTriggerDelay(par):
	print 'TELLIE - Trigger Delay = ', par
	if par <= MAXTDELAY:
		x = par/5
	else:
		print 'WARNING: trigger delay above limit, set to maximum: ', MAXTDELAY
		x = 255
		
	s.write('d'+chr(x))
	time.sleep( wait )
	return


# adjust individual channel delay, on each pulse board
# 0-255, 0.25ns step, max 63.75ns
# returns 'e'
def setChannelDelay(par):
	print 'TELLIE - Fibre Delay = ', par
	if par <= MAXFDELAY:
		e = par*4	
	else:
		print 'WARNING: fibre delay above limit, set to maximum: ', MAXFDELAY
		e = 255
		
	s.write('e'+chr(e))
	time.sleep( wait )
	return


# change master/slave mode (point of view of tellie)
# true/false changed to True/False in json file
def setTellieMaster(istrue):
	if istrue:
		dict['run_list'][isubrun]['ellie_driven'] = True
	else:
		dict['run_list'][isubrun]['ellie_driven'] = False


# change trigger mode (MTCD or generated light)
def setMTCDTrigger(istrue):
	if istrue:
		dict['run_list'][isubrun]['detector_forced_readout'] = True
	else:
		dict['run_list'][isubrun]['detector_forced_readout'] = False


# adjust intensity around standard (individual channel)
# no idea how to do that at the moment... :-|
	


#######################################################################
#
# Settings for the entire TELLIE
#

# trigger delay = on the control box
# among expert mode functions


# load several LEDs after each was declared and initialised
def loadAllChannels(isubrun):
	print 'TELLIE - Load all selected LEDs:'
	ledlist = dict['run_list'][isubrun]['led_selected']
	s.write('C')
	for led in ledlist:
		s.write('J'+chr(led))
		print 'led ', led
	s.write('E')
	return



#######################################################################
#
# Readout operations
#

# read PIN diode once
# returns the pulse height (int)
def readAveragedPIN():
	buffer = s.read(100)
	return buffer


def readPIN(led):
	selectLED(led)
	s.write('r')
	time.sleep(wait)
	buffer = s.read(100)
	return buffer


# Read the temperature sensors
def getTemp(n):
	hi = int(n/10)
	lo = n - (hi*10)
	s.read(50)
	
	s.write('n'+chr(hi)+chr(lo))
	time.sleep(6)
	s.write('T')
	time.sleep(2)
	buffer = s.read(50)
        print buffer
	t = buffer[1:]
	return t
	
	
def readT(box):	
	n=box*3
	t1 = getTemp(n-2)
	t2 = getTemp(n-1)
	t3 = getTemp(n)
	
	list = [t1, t2, t3]
	return list
	

def isReadyToStart():
	buffer = s.read(200)
	print buffer
	return ('CB' in buffer) and ('N' in buffer) and ('LMP' in buffer) and ('QRS' in buffer) and ('e' in buffer) and ('HG' in buffer) and ('u' in buffer) and ('d' in buffer)


# for next version
#
# def isReadyToStartSeveral(n):
# 	# build expected string from init & load of all the leds
# 	initstr = ''
# 	loadstr = 'C'
# 	for i in range(n):
# 		initstr += 'CB1NLMPQRSHGue'
# 		loadstr += 'B1'
# 	loadstr += 'Ed'
# 	initstr += loadstr
# 	buffer = s.read(200)
# 	boolStatus = (initstr == buffer) 
# 	return boolStatus




#######################################################################
#
# Intermediate functions
#

# LED index
def returnChannel(led):
	for i in range(0, len(dict['hw']), 1):
		if dict['hw'][i]['id'] == led:
			return i


# subrun index
def returnSubrun(subrun):
	for i in range(0, len(dict['run_list']), 1):
		if dict['run_list'][i]['id'] == subrun:
			return i


# nb of LED to loop over
def returnNbChannels(isubrun):
	return len(dict['run_list'][isubrun]['led_selected'])


# initialise the individual channel
def initChannel(isubrun, led):
	iled = returnChannel(led)
	
	#channel settings
	height  = dict['hw'][iled]['pulse_height']
	width   = dict['hw'][iled]['pulse_width']
	delay   = dict['hw'][iled]['fibre_delay']
	nbpulses = dict['run_list'][isubrun]['nb_pulses']
	frequency = dict['run_list'][isubrun]['ellie_pulse_rate']
	pulse_delay = 1000./ frequency
	
	selectLED(led)
	setPulseHeight(height)
	setPulseWidth(width)
	setPulseNumber(nbpulses)
	setPulseDelay(pulse_delay)
	setChannelDelay(delay)
	
	
# initialise the subrun, with possibility of several LEDs.
# subrun nb must be above 0
def init(subrun):
	isubrun = returnSubrun(subrun)
	print 'subrun index = ', isubrun

	nbled = returnNbChannels(isubrun)
	print 'nb of led selected = ', nbled
	
	for i in range(0, nbled, 1):
		led = dict['run_list'][isubrun]['led_selected'][i]
		initChannel(isubrun, led)

	if (nbled>1):
		loadAllChannels(isubrun)

	#run settings
	trigger_delay = dict['run_list'][isubrun]['ellie_trigger_delay']
	setTriggerDelay(trigger_delay)	
	
	check = status(nbled)	
	return check


# looped back fibre, subrun nb 0
# led in channel 15
# read out PIN on channels 15 and 16
#
def runMonitoringChannel():
	isubrun = 0
	led = dict['run_list'][isubrun]['led_selected'][0]
	out = dict['run_list'][isubrun]['led_selected'][1]
	
	initChannel(isubrun,led)
	loadAllChannels(isubrun)
	
	# fire
	s.write('g')

	# readout
	print s.read(100)
	monit1 = readPIN(led)
	print monit1[5:]
	monit2 = readPIN(out)
	print monit2[4:]
	return
	

#######################################################################
#
# Other high level functions
#

def status(nbled):
	return isReadyToStart()
# 	if nbled==1:
# 		return isReadyToStart()
# 	else:
# 		return isReadyToStartSeveral(nbled)


# g command doesn't take the counter into account
# use s command instead, read the buffer to get averaged PIN readout
def fire():
	s.write('s')
	return


def stop():
	s.write('X')
	return


def enableExtTrigger():
	s.write('F')
	return






#######################################################################
#
# To do when we import this module
#

# serial port
s = openSerial()

# db file
file = './TELLIE.json'
dict = ReadRATDB(file)
