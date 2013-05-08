
### Orca -> TELLIE command flags:
# Flags notify Tellie of the format of the input
# Should be separated by '|' from JSON settings where appropriate
orca_init = "I" # JSON of settings
orca_fire = "F" # Fire once, or multiple?
orca_stop = "X" # No settings
orca_read = "R" # No settings

#expected types to follow command flags
orca_init_type = dict
orca_fire_type = dict
orca_stop_type = type(None)
orca_read_type = type(None)

### TELLIE -> Orca response flags:
# Flags notify Orca of the format of the output
# Should be separated by '|' from JSON responses where appropriate
tellie_ready = "R" # list of channels prepared
tellie_firing = "F" # no other information
tellie_stopped = "X" # no other information
tellie_pinout = "P" # SHOULD BE dict of channels and PIN readings
tellie_notready = "Z" # response when polled for PIN, but firing incomplete
tellie_error = "E" # Reason string

#expected types 
tellie_ready_type = type(None)
tellie_firing_type = type(None)
tellie_stopped_type = type(None)
tellie_pinout_type = int
tellite_notready_type = type(None)
tellie_error_type = str
