#!/usr/bin/env python
#####################
#
# new_mapping.py
#
# Script to update fibre / channel mapping.
#
#####################

import os
import sys
import optparse
import couchdb
import json
import copy
import time
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


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option('--push', dest='push', help='push a whole new mapping document')
    parser.add_option('--update', dest='update', help='update the current mapping')
    parser.add_option('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_option('-n', dest='name', help='database name [tellie]',
                      default='tellie')
    (options, args) = parser.parse_args()

    database = tellie_database.TellieDatabase.get_instance()
    database.login(options.server, options.name)

    if options.update:
        # Update the current mapping document...
        update_mapping()

    elif options.push:
        # push a new mapping document
        new_mapping(options.push)
