################################################
# Script to upload new calibration files to 
# telliedb. It reads in a results_overview.csv
# produced by TELLIE_calibration_code, pushes
# up a new set of calibration files (channel by
# channel and fireParameter types) and updates
# the old files run range.
#
# Author: Ed Leming <e.leming@sussex.ac.uk>
#
################################################
from orca_side import tellie_database
import couchdb
import csv
import datetime
import pytz
import argparse
import sys
import copy

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_channel_pars(fname):
    '''Read in data from csv file containing all channels results and return a dict
    of the photonVsIPW fit parameters.
    '''
    ipw_dict, pin_dict, fibre_delay = {}, {}, {}
    results = csv.DictReader(open(fname))
    for idx, line in enumerate(results):        
        ipw_dict[int(line['channel'])] = ([float(line['ipw_p0']), float(line['ipw_p1']),
                                       float(line['ipw_p2']), float(line['ipwChi2'])])
        pin_dict[int(line['channel'])] = [float(line['pin_p0']), float(line['pin_p1']), float(line['pinChi2'])]
        if "fibre_delay" in line: # Calibration not yet available, but we're expecting them soon
            fibre_delay[int(line['channel'])] = float(line['fibre_delay'])
    return ipw_dict, pin_dict, fibre_delay

def get_current_docs(db, view):
    '''Return only the most current docs from a passed view
    '''
    current_docs = []
    all_docs = db.get_docs_from_view(view)
    for doc in all_docs:
        if doc["run_range"][1] == 0:
            current_docs.append(doc)
    return current_docs

def create_new_docs(old_docs, ipw_pars, pin_pars, fibre_delay):
    '''Copy old doc and re-format all necessary fields to produce a new calibration
    document. This method is preferable to creating an entiarly new dict and filling 
    from scratch as channel dependent fields like 'cone' will always remain static. 
    We therefore avoid creating some kind of proxy look-up-table to create the
    global look-up-table, which makes my head hurt. 
    '''
    ######################################
    # Get user to define the run range
    try:
        first_valid = int(raw_input('Which run are these calibrations valid from? : '))
    except ValueError as e:
        print bcolors.WARNING + "That wasn't a number!" + bcolors.ENDC
        raise e

    last_valid = raw_input('Which run are these calibrations valid until? If indefinite please set to 0. [0]: ')
    if last_valid is "":
        last_valid = 0
    else:
        try:
            last_valid = int(last_valid)
        except ValueError as e:
            print bcolors.WARNING + "That wasn't a number!" + bcolors.ENDC
            raise e

    new_docs = []
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
    for i, doc in enumerate(old_docs):
        new_doc = copy.copy(doc)
        channel = int(doc["channel"])
        del new_doc["_id"]
        del new_doc["_rev"]
        if "patch" in new_doc: # If it's an old version, get rid of redundent fields
            del new_doc["patch"]
        if "Eq_10Hz" in new_doc:
            del new_doc["Eq_10Hz"]
            del new_doc["Eq_1kHz"]
            del new_doc["Pars_10Hz"]
            del new_doc["Pars_1kHz"]
        if fibre_delay: # If time calibrations are passed, update them
            new_doc["fibre_delay"] = fibre_delay[channel]
        new_doc["Eq_ipw_10Hz"] = "poly2"
        new_doc["Eq_ipw_1kHz"] = "poly2"
        new_doc["Eq_pin_10Hz"] = "poly1"
        new_doc["Eq_pin_1kHz"] = "poly1"
        new_doc["Pars_ipw_10Hz"] = [0, 0, 0]
        new_doc["Pars_ipw_1kHz"] = ipw_pars[channel][0:3]
        new_doc["Pars_pin_10Hz"] = [0, 0, 0]
        new_doc["Pars_pin_1kHz"] = pin_pars[channel][0:2]
        new_doc["Chi2_ipw_10Hz"] = 0
        new_doc["Chi2_ipw_1kHz"] = ipw_pars[channel][3]
        new_doc["Chi2_pin_10Hz"] = 0
        new_doc["Chi2_pin_1kHz"] = pin_pars[channel][2]
        new_doc["timestamp"] = timestamp
        new_doc["version"] = 2
        new_doc["run_range"] = [first_valid, last_valid]
        new_docs.append(new_doc)
    return new_docs

def create_new_fire_parameters(new_docs):
    '''Create a dict represeting a new fire parameters document using the passed ipw_pars.
    This document is simply a summary of the individual channel calibration documents so
    is crated with the same run range and last_valid. 
    '''
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()

    fire_doc = {}
    fire_doc["comment"] = ""
    fire_doc["index"] = ""
    fire_doc["pass"] = 0
    fire_doc["version"] = 2
    fire_doc["production"] = True
    fire_doc["last_valid"] = new_docs[0]["run_range"][1]
    fire_doc["run_range"] = new_docs[0]["run_range"]
    fire_doc["timestamp"] = timestamp
    fire_doc["type"] = "fire_parameters"
    for doc in new_docs:
        channel_fields = {}
        channel = int(doc["channel"])
        channel_fields["channel"] = channel
        channel_fields["fibre_delay"] = doc["fibre_delay"]
        channel_fields["pulse_height"] = doc["pulse_height"]
        channel_fields["Eq_ipw_10Hz"] = doc["Eq_ipw_10Hz"] 
        channel_fields["Eq_ipw_1kHz"] = doc["Eq_ipw_1kHz"] 
        channel_fields["Pars_ipw_10Hz"] = doc["Pars_ipw_10Hz"]
        channel_fields["Pars_ipw_1kHz"] = doc["Pars_ipw_1kHz"]
        fire_doc["channel_%i" % channel] = channel_fields
    return fire_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_argument('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    parser.add_argument('-f', dest='file', help='.csv file to be converted to a mapping doc')
    args = parser.parse_args()

    # Get reference to the tellie database
    db = tellie_database.TellieDatabase(args.server, args.database)
    # Find current calibration documents
    current_docs = get_current_docs(db, "_design/channels/_view/channel_by_number")
    # Find current fireParameters document
    current_fire_parameters = get_current_docs(db, "_design/tellieQuery/_view/fetchFireParameters")
    current_fire_parameters = current_fire_parameters[0]

    # Create new calibration document using old file as template
    ipw_pars, pin_pars, fibre_delay = get_channel_pars(args.file)
    new_docs = create_new_docs(current_docs, ipw_pars, pin_pars, fibre_delay)
    # Create a new fireParameters document using fields from the new calibration docs
    new_fire_parameters = create_new_fire_parameters(new_docs)

    # Save new files to telliedb
    db.save(new_fire_parameters)
    for doc in new_docs:
        db.save(doc)

    # Update old files
    update_fields = {}
    update_fields["run_range"] = [current_docs[0]["run_range"][0], new_docs[0]["run_range"][0] - 1] 
    for doc in current_docs:
        db.update_doc(doc["_id"], update_fields)
    # fire parameters document also requires the last_valid to be updated
    update_fields["last_valid"] = new_docs[0]["run_range"][0] - 1
    db.update_doc(current_fire_parameters["_id"], update_fields)

