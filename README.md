# TELLIE

A set of modules and scripts for use with the SNO+ TELLIE calibration system.

## Usage

Before running any of these scripts, the correct environment should be setup by changing directory to the top TELLIE directory and running:

source env.sh

TELLIE scripts communicate over sockets.  The main control script (bin/tellie.py) must be started on a machine that is connected to the TELLIE USB/serial interface:

python bin/tellie.py

Until an Orca interface is developed to control TELLIE, commanding is achieved via a GUI that should be run (once the main control script is running) via:

python orca_side/fake_gui.py

By default this assumes that the control script is running on the same machine.  If running on a remote machine, the -a option should be used with an argument of the IP address of the machine running the control script.

## Testing Directory

A directory containing scripts used to test and characterise the response of the TELLIE system.  Not intended for regular use.


## Commands List for SNOC6.hex

```c
if (x=='a') continuous(); /*Fires contiously*/
if (x=='b') extaverage(); ?
if (x=='p') extaverage2(); ?
if (x=='c') cleardisp(); ?
if (x=='d') triggerdelay(); /*Set trigger delay 5*(0-255)ns*/
if (x=='e') fibrelengthdelay(); /*Set fibre delay 0.25*(0-255)ns*/
if (x=='g') run(); ?
if (x=='h') secdelay(); ?
if (x=='i') secenable(); ?
if (x=='j') secdisable(); ?
if (x=='C) zero(); /*Clear channel*/
if (x=='H') numberhi(); /*Sets number of pulses hi 0-255*/
if (x=='G') numberlo(); /*Sets number of pulses lo 0-255 n.b. no of pulses = hi*lo*/
if (x=='I') singleselect(); Select single channel start 
if (x=='J') multipleselect(); /*Select multiple channels start*/
if (x=='N') load(); /*Select single channel end*/
if (x=='D') loaddel(); ?
if (x=='E') loadmulti(); /*Select multiple channel end*/
if (x=='L') heighthi(); /*Set IOP hi 0-63*/
if (x=='M') heightlo(); /*Set IOP lo 0-255*/
if (x=='P') loadheight(); /*Load IOP = (hi*256)+lo*/
if (x=='Q') widthhi(); /*Set IPW hi 0-63*/
if (x=='R') widthlo(); /*Set IPW lo 0-255*/
if (x=='S') loadwidth(); /*Load IPW = (hi*256)+lo*/
if (x=='r') pulseheightout(); /*Read PIN once of channel (lower boxes 1-7)*/
if (x=='s') averagedph(); /*Read averaged PIN of channel (lower boxes 1-7)*/
if (x=='m') pulseheightout2(); /*Read PIN once of channel (higher boxes 8-13)*/
if (x=='U') averagedph2(); /*Read averaged PIN of channel (higher boxes 8-13)*/
if (x=='u') usdelay(); /*set pulse delay (microseconds)*/
if (x=='A') extrigenable(); ?
if (x=='B') extrigdisable(); ?
if (x=='F') extrigger(); ?
if (x=='n') therm=db18b20select(); /*select thermometer (lower boxes 1-7)*/
if (x=='T') ds18b20_read(therm); /*read thermometer (lower boxes 1-7)*/
if (x=='f') therm2=db18b20select2(); /*select thermometer (higher boxes 8-13)*/
if (x=='k') ds18b20_read2(therm2); /*read thermometer (higher boxes 8-13)*/
```
