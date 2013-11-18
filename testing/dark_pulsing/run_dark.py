

def send_pulses(sc, channel, width, number):
    sc.select_channel(channel)
    sc.set_pulse_width(width)
    sc.set_pulse_number(number)
    sc.fire_sequence()
    # Need to know when to read the pin    
    sequence_time = sc.get_pulse_delay() * sc.get_pulse_number() # ms
    time.sleep((sequence_time + 0.2) * 0.001) # Add 200us offset
    pin_out = None
    while pin_out is None:
        pin_out, channel_list = sc.read_pin_sequence()
    



if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", dest="channel", type="int", help="Channel number")
    parser.add_option("-w", dest="width", type="int", help="Pulse width")
    parser.add_option("-p", dest="port", help="Serial port")
    (options, args) = parser.parse_args()
    
    # Start pulsing
    sc = serial_command.SerialCommand(options.port)

    # Setup the initial settings
    sc.select_channel(options.channel)
    sc.set_pulse_height(16383)
    sc.set_trigger_delay(0)
    sc.set_fibre_delay(0)
    sc.set_pulse_delay(0.001)
    
    # Loop over lots of times...
    
    # Dark
    send_pulses(sc, options.channel, 16383, 1000)
    # Light
    send_pulses(sc, options.channel, options.width, 1)
