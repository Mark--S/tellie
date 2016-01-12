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

def get_int_from_string(string):
    return int(re.search(r'\d+', string).group())

def get_ints_from_paths(path_array):
    ints = []
    for path in path_array:
        ints.append(get_int_from_string(path))
    return ints

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="baseDirec", 
                        help="Base directory of channel calibration files",
                        type=str, 
                        required=True)
    args = parser.parse_args()

    versions = get_ints_from_paths(os.listdir(args.baseDirec))
    for version in versions:
        path_str = "%s/version_%i/" % (args.baseDirec, version)
        pass_nos = get_ints_from_paths(os.listdir(path_str))
        for pass_no in pass_nos:
            print "%s/version_%i/pass_%i" % (args.baseDirec, version, pass_no)
            
