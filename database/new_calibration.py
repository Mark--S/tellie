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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_channel_fit_pars(fname):
    '''Read in data from csv file containing all channels results and return a dict
    of the photonVsIPW fit parameters.
    '''
    ipw_dict, pin_dict = {}, {}
    results = csv.DictReader(open(fname))
    for idx, line in enumerate(results):        
        ipw_dict[int(line['channel'])] = ([float(line['ipw_p0']), float(line['ipw_p1']),
                                       float(line['ipw_p2']), float(line['ipwChi2'])])
        pin_dict[int(line['channel'])] = [float(line['pin_p0']), float(line['pin_p1']), float(line['pinChi2'])]
    return ipw_dict, pin_dict

def get_current_docs(db):
    '''Return only the most current docs from the channel_by_number view
    '''
    current_docs = []
    all_docs = db.get_docs_from_view("_design/channels/_view/channel_by_number")
    for doc in all_docs:
        if doc["run_range"][1] == 0:
            current_docs.append(doc)
    return current_docs

def get_ids(docs):
    '''Return an array containing the ids of each doc in the passed 'docs' array
    '''
    _ids = []
    for doc in docs:
        _ids.append(doc["_id"])
    return _ids

def create_new_docs(old_docs, ipw_pars, pin_pars):
    '''Create new dictionaries containing all necessary fields for a new calibration docuement
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
    for i, doc in enumerate(old_docs):
        new_doc = doc
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
        new_doc["version"] = 2
        new_doc["run_range"] = [first_valid, last_valid]
        new_docs.append(new_doc)
    return new_docs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_argument('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    parser.add_argument('-f', dest='file', help='.csv file to be converted to a mapping doc')
    args = parser.parse_args()

    # Get calibration information from file
    ipw_pars, pin_pars = get_channel_fit_pars(args.file)

    # Get reference to the database
    db = tellie_database.TellieDatabase(args.server, args.database)
    current_docs = get_current_docs(db)
    current_doc_ids = get_ids(current_docs)

    new_docs = create_new_docs(current_docs, ipw_pars, pin_pars)

    _id, _rev = db.save(new_docs[0])
    raw_input("Hit enter to delete the doc: ")
    db.delete(_id)
