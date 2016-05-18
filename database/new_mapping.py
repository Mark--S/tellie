#!/usr/bin/env python
####################################################
# new_mapping.py
# Script to update fibre / channel mapping.
#
# Author: Ed Leming <e.leming@sussex.ac.uk>
####################################################
import csv
import pytz
import os
import sys
import argparse
import couchdb
import json
import copy
import time
import datetime
import calendar
from orca_side import tellie_database


def update_mapping():
    database = tellie_database.TellieDatabase.get_instance()
    rows = database.db.view('_design/channels/_view/mapping_by_date', descending=True,
                            limit=1, include_docs=True) # Gets the latest mapping document
    doc = None
    for row in rows:
        doc = row.doc
    print "CURRENT MAPPING:"
    print "CHAN\tPATCH\tFIBRE"
    #TODO: should sort these!
    #TODO: don't overwrite old doc; write a new one!
    for i, _ in enumerate(doc['channels']):
        print "%s\t%s\t%s" % (doc['channels'][i], doc['patches'][i], doc['fibres'])

    new_doc = copy.copy(doc) # So that we can compare and check no duplicate channels or fibres
    update = True
    while update is True:
        channel = int(raw_input("Channel to update: "))
        patch = raw_input("Patch for %03d (currently %s): " % (channel, doc['patches'][channels.index(channel)]))
        fibre = raw_input("Fibre for %03d (currently %s): " % (channel, doc['fibres'][channels.index(channel)]))
        index = new_doc['channels'].index(channel)
        new_doc['patches'][index] = patch
        new_doc['fibres'][index] = fibre
        more = raw_input("Update another channel (no results saved yet!)? [y/N]: ")
        if more!='y' and more!='Y':
            update = False
    # Now check for duplicates
    ok = True
    for i, _ in enumerate(doc['channels']):
        channel = doc['channels'][i]
        patch = doc['patches'][i]
        fibre = doc['fibres'][i]
        n_channels = doc['channels'].count(channel)
        n_patches = doc['channels'].count(patch)
        n_fibre = doc['channels'].count(fibre)
        if n_channels > 1 or n_patches > 1 or n_fibres > 1:
            print "Cannot update, duplicates for %s / %s / %s" % (channel, patch, fibre)
            ok = False
    if ok is True:
        database.save(new_doc)


def boxes_to_channels(mapping):
    channels = []
    for i, _ in enumerate(mapping['boxes']):
        channel = mapping['boxes'][i] * 8 + mapping['box_channels'][i] + 1
        channels.append(channel)
    return channels


def new_mapping(filename):
    database = tellie_database.TellieDatabase.get_instance()
    fin = file(filename, 'r')
    mapping = json.load(fin)
    # Check the correct fields are present, if not then convert box number/channel to channel number
    if 'patches' not in mapping:
        raise Exception("Must have patches in mapping doc")
    if 'fibres' not in mapping:
        raise Exception("Must have fibres in mapping doc")
    if 'channels' not in mapping:
        if 'boxes' not in mapping or 'box_channels' not in mapping:
            raise Exception("Must have channels or boxes/box_channels in mapping doc")
        # Convert from boxes to channels
        mapping['channels'] = boxes_to_channels(mapping)
        mapping.pop('boxes')
        mapping.pop('box_channels')
    # Check the timestamp
    if 'timestamp' not in mapping:
        use_now = raw_input("Use current time?[Y/n]: ")
        if use_now=='n' or use_now=='N':
            time_set = raw_input("Enter unix timestamp or yyyy:mm:dd hh:mm:ss format: ")
            try:
                time_set = float(time_set)
            except ValueError:
                time_structure = time.strptime(time_set, "%Y:%m:%d %H:%M:%S")
                time_set = float(calendar.timegm(time_structure))
            mapping['timestamp'] = time_set
        else:
            mapping['timestamp'] = time.time()
    mapping['pass'] = 0
    mapping['type'] = 'mapping'
    docid, revision = database.save(mapping)
    print "Saved as %s" % docid

def load_json(path):
    '''Load a json files into a python dictionary
    :param: Path .json file to load.
    :returns: Dictionary containing json data, keys are the json labels
    '''
    with open('%s' % (path), 'r') as json_file:
        json_data = json.load(json_file)
    return json_data

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
        print "That wasn't a number!"
        raise e

    last_valid = raw_input('Which run is this patch map valid until? If indefinite please set to 0. [0]: ')
    if last_valid is "":
        last_valid = 0
    else:
        try:
            last_valid = int(last_valid)
        except ValueError as e:
            print "That wasn't a number!"
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

def check_last_mapping(db, new_doc):
    '''Find the any current mapping doc on the db with last_valid set to 0
    '''
    docs = db.get_docs_from_view("_design/tellieQuery/_view/fetchCurrentMapping")
    for doc in docs:
        if "last_valid" in doc:
            print "_id:\t\t%s\nlast_valid:\t%s\n" % (doc["_id"], doc["last_valid"])

        if doc["last_valid"] == 0:
            request = raw_input("Document %s currently has infinite validity, would you like to update it? [Y/n] : ")
            if request == "Y" or request == "y" or request == "":
                update_defualt = raw_input("Update last_valid to %s [Y/n] : " % (new_doc['run_range'][0]-1))
                if update_default == "Y" or update_default == "y" or update_defauly == "":
                    update_fields["last_valid"] = new_doc["run_range"][0]
                    update_fields["run_range"] = [doc["run_range"][0], (new_doc["run_range"][0]-1)]
                else:
                    try:
                        user_valid = int(raw_input("What would you like to update to? "))
                    except ValueError as e:
                        print "That wasn't a number!"
                        raise e
                    update_fields["last_valid"] = user_valid
                    update_fields["run_range"] = [doc["run_range"][0], user_valid]
                update_mapping(db, _id, update_fields)
                    
def update_mapping(db, _id, update_fields):
    '''Update document of type _id with fields in new_dict
    '''
    old_doc = db.load_doc(_id)
    new_doc = {}
    for key in doc.keys:
        if key in update_fields:
            new_doc[key] = update_fields[key]
        else:
            new_doc[key] = old_doc[key]
    db.save(new_doc)
    print "Document %s updated!" % _id

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_argument('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--push', dest='push', help='push a whole new mapping document')
    group.add_argument('--update', dest='update', help='update the current mapping')
    args = parser.parse_args()

    if args.push:
        #new_doc = make_mapping_dict(args.push)

        db = tellie_database.TellieDatabase(args.server, args.database)
        # Check if a doc currently exists on the db with infinite validity
        _id = check_last_mapping(db, new_doc)
        sys.exit()

    elif args.update:
        # push a new mapping document
        # new_mapping(options.push)
        print "Exiting...."
