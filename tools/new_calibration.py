'''A python script to read in the current hardware
status .csv and performance summary files produced
from the channel calibration data using 
createSummaryFile.py. 

Hardware status gsheet:

https://docs.google.com/spreadsheets/d/1m6w9x162qPbO0EpruCQORSqrlMgiGSu35oala6uIpp0/edit#gid=0

Author: Ed Leming
Date: 17 / 11 / 2016
'''
from orca_side import tellie_database
import re
import csv
import datetime
import pytz
import json
import optparse
import sys

rat_infinity = 2147483647

def read_hardware_status(fname):
    '''Read in relavent fields from Sofia's install table
    '''
    channel = []
    driver = {}
    PIN = {}
    cone = {}
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        next(reader, None) # Skip header lines
        next(reader, None)
        next(reader, None)
        next(reader, None)
        for i, row in enumerate(reader):
            if int(row[0]) == 96:
                continue
            channel.append(int(row[0]))
            driver[channel[i]] = int(re.search(r'\d+', row[1]).group())
            PIN[channel[i]] = row[2]
            cone[channel[i]] = row[3]
    return channel, driver, PIN, cone

def read_calib_summary(fname):
    '''Read in a calibration summary file produced by Mark's
    newly generated scripts.
    '''
    with open (fname, "r") as calibFile:
        calibData=calibFile.readlines()
    channelStrings = ['{'+x+'}' for x in calibData[0].strip('{}').split('}{')]

    channelDicts = []
    for channelString in channelStrings:
        channelDicts.append(json.loads(channelString))

    longest_offset = 0
    for channel in channelDicts:
        if channel['timing_offset'] > longest_offset:
            longest_offset = channel['timing_offset']

    for channel in channelDicts:
        # Use longest offset to define a fibre delay, quantised to 0.25ns
        channel["fibre_delay"] = round(((longest_offset - channel['timing_offset'])*1e9)*4)/4.
        channel["IPW"] = channel["ipws"]
        channel["PIN"] = channel["pins"]
        channel["PIN_rms"] = channel["pin_errors"]
        channel["photons_per_pulse"] = channel["photon_counts"]
        channel["photons_per_pulse_rms"] = channel["photon_count_errors"]
        # Delete unwanted fields
        del channel['timing_offset']
        del channel['index']
        del channel['timestamp']
        del channel['ipws']
        del channel['pins']
        del channel['pin_errors']
        del channel['photon_counts']
        del channel['photon_count_errors']
    return channelDicts
        
def make_calibration_files(hardware_file, slave_file, master_file, valid_from):
    '''Use channel hardware status file and master / slave mode 
    calibration summary files to produce a new set of 
    channel-to-channel calibration files for the database.
    '''
    channel, driver_labels, PIN_labels, cone_labels = read_hardware_status(hardware_file)
    slave_settings = read_calib_summary(slave_file)
    master_settings =  read_calib_summary(master_file)
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()

    # Make a doc for each channel
    calib_docs = []
    for i, chan in enumerate(channel):
        new_doc = {}
        # Add manditory fields for ratdb
        new_doc["type"] = "TELLIE_CAL"
        new_doc["index"] = ""
        new_doc["version"] = 0
        new_doc["pass"] = -2 # This makes it an 'online' doc type when pushed to ratdb.
        new_doc["timestamp"] = timestamp
        new_doc["comment"] = ""
        new_doc["run_range"] = [valid_from, rat_infinity]

        # Add hardware descriptions
        new_doc["channel"] = chan
        new_doc["driver"] = driver_labels[chan]
        new_doc["PIN_board"] = PIN_labels[chan]
        new_doc["cone"] = cone_labels[chan]

        if master_settings[i]["channel"] != chan or slave_settings[i]["channel"] != chan:
            raise "LOOPS ARE OUT OF SYNC, EXITING"

        # Add channel depanedent delays
        new_doc["fibre_delay"] = master_settings[i]["fibre_delay"]

        # Add master mode calibrations
        new_doc["master_IPW"] = master_settings[i]["IPW"]
        new_doc["master_photons"] = master_settings[i]["photons_per_pulse"]
        new_doc["master_photons_rms"] = master_settings[i]["photons_per_pulse_rms"]
        new_doc["master_PIN"] = master_settings[i]["PIN"]
        new_doc["master_PIN_rms"] = master_settings[i]["PIN_rms"]

        # Add slave mode calibrations
        new_doc["slave_IPW"] = slave_settings[i]["IPW"]
        new_doc["slave_photons"] = slave_settings[i]["photons_per_pulse"]
        new_doc["slave_photons_rms"] = slave_settings[i]["photons_per_pulse_rms"]
        new_doc["slave_PIN"] = slave_settings[i]["PIN"]
        new_doc["slave_PIN_rms"] = slave_settings[i]["PIN_rms"]
        
        calib_docs.append(new_doc)
    return calib_docs

def make_fire_parameters_file(calib_docs, first_valid):
    '''Make a new fire parameters file using newly
    created calibration files. The fire parameters file
    provides a summary of the ipw vs photons curves for
    each tellie channel. This file is read by ORCA when
    applying intensity settings.
    '''
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()

    fire_doc = {}
    fire_doc["type"] = "TELLIE_FIRE_PARS"
    fire_doc["comment"] = ""
    fire_doc["index"] = ""
    fire_doc["pass"] = 0
    fire_doc["version"] = 0
    fire_doc["first_valid"] = first_valid
    fire_doc["run_range"] = [first_valid, rat_infinity]
    fire_doc["timestamp"] = timestamp
    for doc in calib_docs:
        channel_fields = {}
        channel = doc["channel"]
        channel_fields["fibre_delay"] = doc["fibre_delay"]
        channel_fields["slave_IPW"] = doc["slave_IPW"]
        channel_fields["slave_photons"] = doc["slave_photons"]
        channel_fields["master_IPW"] = doc["master_IPW"]
        channel_fields["master_photons"] = doc["master_photons"]
        fire_doc["channel_%i" % channel] = channel_fields
    return fire_doc

def get_current_docs(db, view):
    '''Return only the most current docs from a passed view
    '''
    current_docs = []
    all_docs = db.get_docs_from_view(view)
    for doc in all_docs:
        if doc["run_range"][1] == rat_infinity:
            current_docs.append(doc)
    return current_docs


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-a",dest="hardware_status",
                      help="Path to csv file detailing the current hardware status. .csv can be made from the link in the comment string at the top of this script.",
                      default="Tellie_hardware_status.csv")
    parser.add_option("-b",dest="slave_data",
                      help="Path to data file containing slave mode response of tellie channels. This file is produced using TELLIE_calibration_code/createSummaryFile.py",
                      default="slave_data.dat")
    parser.add_option("-c",dest="master_data",
                      help="Path to data file containing master mode response of tellie channels. This file is produced using TELLIE_calibration_code/createSummaryFile.py.",
                      default="master_data.dat")
    parser.add_option("-v",dest="valid_from", type=int,
                      help="First run from which these calibrations are valid")
    parser.add_option('-t', dest='tellie_server', help='tellie database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_option('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    (options,args) = parser.parse_args()
    if not options.valid_from:
        parser.error("The the -v flag is a required field. \nFor help try:$ python produce_calibration_files.py --help\n")

    ########################################
    # Make new documents
    ########################################
    print "Making new TELLIE_CAL and TELLIE_FIRE_PARS documents..."
    calib_docs = make_calibration_files(options.hardware_status, options.slave_data, options.master_data, options.valid_from)
    new_fire_parameters = make_fire_parameters_file(calib_docs, options.valid_from)

    request = raw_input("Would you like to save the new set of documents to the database? [Y/n] : ")
    if request != "Y" and request != "y" and request != "":
        print "Exiting..."
        sys.exit()

    ######################################
    # Get reference to the tellie database
    ######################################
    db = tellie_database.TellieDatabase(options.tellie_server, options.database)

    ############################
    # Save new files to db
    ############################
    print "Saving files...."
    db.save(new_fire_parameters)
    for doc in calib_docs:
        db.save(doc)

    #####################################
    # See if any current documents exist
    #####################################
    current_docs = get_current_docs(db, "_design/channels/_view/channel_by_number")
    current_fire_parameters = get_current_docs(db, "_design/tellieQuery/_view/fetchFireParameters")

    ############################
    # Update old files
    ############################
    if current_docs:
        request = raw_input("Another set of channel calibration documents currently have infinite validity, would you like to update them? [Y/n] : ")
        if request == "Y" or request == "y" or request == "":
            update_fields = {}
            update_fields["run_range"] = [current_docs[0]["run_range"][0], options.valid_from - 1]
            for doc in current_docs:
                db.update_doc(doc["_id"], update_fields)

    if current_fire_parameters:
        request = raw_input("Another fireParameter document (%s) currently has infinite validity, would you like to update it? [Y/n] : " % current_fire_parameters[0]["_id"])
        if request == "Y" or request == "y" or request == "":
            db.update_doc(current_fire_parameters[0]["_id"], update_fields)
