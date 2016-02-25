'''Script to create a fire_parameters json file.
This file summarises the tellie fire parameters on
a channel by channel basis. 

This script checks the directory structure from a
provided base directory and creates a fire_parameters
file for each version & pass.
'''
import json
import argparse
import os
import re
import datetime
import pytz
import sys

def get_int_from_string(string):
    return int(re.search(r'\d+', string).group())

def get_ints_from_paths(path_array):
    ints = []
    for path in path_array:
        ints.append(get_int_from_string(path))
    return ints

def reduce_json(json_dict):
    '''Delete unwanted fields from channel dict
    '''
    mod_dict = json_dict
    if 'cavity' in mod_dict:
        del mod_dict['cavity']
    if 'comment' in mod_dict:
        del mod_dict['comment']
    if 'cone' in mod_dict:
        del mod_dict['cone']
    if 'driver' in mod_dict:
        del mod_dict['driver']
    if 'index' in mod_dict:
        del mod_dict['index']
    if 'patch' in mod_dict:
        del mod_dict['patch']
    if 'type' in mod_dict:
        del mod_dict['type']
    if 'production' in mod_dict:
        del mod_dict['production']
    if 'timestamp' in mod_dict:
        del mod_dict['timestamp']
    if 'run_range' in mod_dict:
        del mod_dict['run_range']
    if 'index' in mod_dict:
        del mod_dict['index']
    return mod_dict

def check_dir(dname):
    '''Check if directory exists, create it if it doesn't'''
    direc = os.path.dirname(dname)
    try:
        os.stat(direc)
    except:
        os.mkdir(direc)
        print 'Made directory %s....' % dname
    return direc

def load_json(path):
    '''Load a json files into a python dictionary
    :param: Path .json file to load.
    :returns: Dictionary containing json data, keys are the json labels
    '''
    with open('%s' % (path), 'r') as json_file:
        json_data = json.load(json_file)
    return json_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="baseDirec", 
                        help="Base directory of channel calibration files",
                        type=str, 
                        required=True)
    args = parser.parse_args()
    # find how many versions we have and loop over them
    versions = get_ints_from_paths(os.listdir(args.baseDirec))
    for version in versions:
        path_str = "%s/version_%i/" % (args.baseDirec, version)
        pass_nos = get_ints_from_paths(os.listdir(path_str))
        # find how many passes we have for this version and loop
        for pass_no in pass_nos:
            # Set-up master dictionary
            master_dictionary = dict()
            timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
            master_dictionary['type'] = 'fire_parameters'
            master_dictionary['timestamp'] = timestamp
            master_dictionary['production'] = 'true'
            master_dictionary['index'] = ''
            master_dictionary['comment'] = ''
            master_dictionary['pass'] = pass_no
            master_dictionary['version'] = version
            # Find all files for this version / pass
            full_path = "%s/version_%i/pass_%i/" % (args.baseDirec, version, pass_no)
            files = os.listdir(full_path)
            for f in files:
                file = "%s%s" % (full_path, f)
                channel_json = load_json(file)
                if not 'run_range' in master_dictionary:
                    if 'run_range' in channel_json:
                        master_dictionary['run_range'] = channel_json['run_range']
                        master_dictionary['last_valid'] = channel_json['run_range'][1]
                chan_no = get_int_from_string(f)
                # Get rid of unwanted stuff and add to master dict
                master_dictionary['Channel_%i' % chan_no] = reduce_json(channel_json)

            version_str = check_dir('./default_database/fire_parameters/version_%i/' % version)
            pass_str = check_dir('%s/pass_%i/' % (version_str, pass_no))
            save_str = '%s/fire_parameters.js' % pass_str
            # Save to file
            with open(save_str, 'w+') as json_file:
                print 'Creating %s' % save_str
                json_file.write(json.dumps(master_dictionary))
                json_file.close()
            
