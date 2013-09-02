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