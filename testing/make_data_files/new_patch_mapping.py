'''Script to create a new mapping doc using a standardised .json
file format and channel, patch, fibre info from a csv file.
Files created by this script can be pushed up to the telliedb
using tellie/bin/database/push_db.py
'''

import csv
import json
import os
import optparse
import datetime
import pytz
from orca_side import tellie_database

def check_dir(dname):
    '''Check if directory exists, create it if it doesn't'''
    direc = os.path.dirname(dname)
    try:
        os.stat(direc)
    except:
        os.mkdir(direc)
        print 'Made directory %s....' % dname
    return dname

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
    :retruns: 4D list of 
    '''
    channel, patch, fibre = [], [], []
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if idx == 0:
                continue
            channel.append(row[0])
            patch.append(row[1])
            fibre.append(row[2])
    return channel, patch, fibre

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-f', dest='file',
                      help='.csv file to be loaded.')
    parser.add_option('-p', dest='path',
                      default='./default_database/mapping/',
                      help='Path to ./default_database/mapping/ direc')
    parser.add_option('-v', dest='version', default=1,
                      help='Version of the calibration file type to be created - 1 by default')
    parser.add_option('--pass', dest='pass_no', default=0,
                      help='Pass number of file - 0 by default')
    (options,args) = parser.parse_args()
    pass_no = int(options.pass_no)
    version = int(options.version)
    if version > 1: 
        print 'This script has been written to update to the specific ratdb compatible' 
        print 'format as of Sept 2015. A new function will have to be written for any' 
        print 'newer revisions to the ratdb compatibility requirements.'

    # Get user input
    low_range = int(raw_input('Please enter the first run for which this patching was valid: '))
    up_range = int(raw_input('Please enter the final run this patching was valid for [1e6]: '))
    if up_range == '':
        up_range = 1e6


    if up_range = 1e6: 
        # Check db for pervious 'permanent' patchings.
        database = tellie_database.TellieDatabase.get_instance()
        database.login('http://couch.snopl.us', 'telliedb')
        database.get_db_view(

    read_csv_patch_map(options.file)
    raise

    # Check directory structure...
    # Check version dir exists
    path_to_version = check_dir('%sversion_%i/' % (options.path, version))
    save_path = check_dir('%spass_%i/' % (path_to_version, pass_no))

    # Read in old files and update
    if version == 1:
            with open('%s%s' % (save_path, file), 'w+') as json_file:
                json_file.write(json.dumps(updated_dict))
                json_file.close()
    print 'Converted all files from %s/version_0/pass_0/' % (options.path)
        
