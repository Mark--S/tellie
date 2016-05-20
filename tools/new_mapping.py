#!/usr/bin/env python
####################################################
# new_mapping.py
# Script to update fibre / channel mapping.
#
# Author: Ed Leming <e.leming@sussex.ac.uk>
####################################################
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


def read_csv_patch_map(fname):
    '''Import csv file containing Channel->Patch->Fibre mapping.
    :param: File name
    :retruns: 3D list of 
    '''
    channel, patch, fibre = [], [], []
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if row[0] == "Fibres" or row[0] == "Fibre":
                fibre_index = 0
                channel_index = 2
                continue
            elif row[0] == "Channel" or row[0] == "Channels":
                channel_index = 0
                fibre_index = 2
                continue
            elif idx == 0:
                continue
            channel.append(row[channel_index])
            patch.append(row[1])
            fibre.append(row[fibre_index])
    return channel, patch, fibre

def make_mapping_dict(fname):
    '''Make a python dictionary to represent the doc that's going to
       be pushed to the database.
    '''
    document = {}
    try:
        first_valid = int(raw_input('Which run is this patch map valid from? : '))
    except ValueError as e:
        print bcolors.WARNING + "That wasn't a number!" + bcolors.ENDC
        raise e

    last_valid = raw_input('Which run is this patch map valid until? If indefinite please set to 0. [0]: ')
    if last_valid is "":
        last_valid = 0
    else:
        try:
            last_valid = int(last_valid)
        except ValueError as e:
            print bcolors.WARNING + "That wasn't a number!" + bcolors.ENDC
            raise e

    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
    channels, patches, fibres = read_csv_patch_map(fname)
    document['type'] = 'mapping'
    document['index'] = ""
    document['timestamp'] = timestamp
    document['version'] = 0
    document['pass'] = 1
    document['production'] = True
    document['run_range'] = [first_valid, last_valid]
    document['last_valid'] = last_valid #This is to allow a simple couch key search for current mapping
    document['channels'] = channels
    document['patches'] = patches
    document['fibres'] = fibres
    document['comment'] = ""
    return document

def check_old_mappings(db, new_doc):
    '''Find the any current mapping doc on the db with last_valid set to 0
    '''
    docs = db.get_docs_from_view("_design/tellieQuery/_view/fetchCurrentMapping")
    for doc in docs:
        if doc["_id"] == new_doc["_id"]: # DON'T UPDATE THE DOC WE JUST PUSHED UP
            continue 
        elif "last_valid" not in doc:
            continue

        if doc["last_valid"] == 0:
            #print "\n_id:\t\t%s\nlast_valid:\t%s\n" % (doc["_id"], doc["last_valid"])
            request = raw_input("Another document (%s) currently has infinite validity, would you like to update it? [Y/n] : " % doc["_id"])
            if request == "Y" or request == "y" or request == "":
                try:
                    user_valid = int(raw_input("What was the last run number this mapping was valid? If you haven't already check the shift reports for the last running period. "))
                except ValueError as e:
                    print bcolors.WARNING + "That wasn't a number!" + bcolors.ENDC
                    raise e
                update_fields = {}
                update_fields["last_valid"] = user_valid
                update_fields["run_range"] = [doc["run_range"][0], user_valid]
                db.update_doc(doc["_id"], update_fields)
                print bcolors.WARNING + "Updated document %s with new run_range and last_valid" % doc["_id"] + bcolors.ENDC
            else:
                print bcolors.WARNING + "WARNING: ORCA will error if there are two mappings with last_valid = 0. You will have to update by hand at:\n\nhttp://couch.snopl.us/_utils/database.html?telliedb/_design/mapping/_view/map_by_run\n" + bcolors.ENDC


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_argument('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    parser.add_argument('-f', dest='file', help='.csv file to be converted to a mapping doc')
    args = parser.parse_args()

    # Connect to database
    db = tellie_database.TellieDatabase(args.server, args.database)

    # Make a new mapping doc from .csv file
    new_doc = make_mapping_dict(args.file)
    
    # Save doc to the db
    _id, _rev = db.save(new_doc)
    new_doc["_id"] = _id
    new_doc["_rev"] = _rev
    
    # Check if a doc currently exists on the db with infinite validity
    check_old_mappings(db, new_doc)
