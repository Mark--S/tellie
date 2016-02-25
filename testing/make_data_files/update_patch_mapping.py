'''Script to create a new mapping doc using a standardised .json
file format and channel, patch, fibre info from a csv file.
Files created by this script can be pushed up to the telliedb
using tellie/bin/database/push_db.py
'''

import json
import os
import optparse
import datetime
import pytz

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

def ratify_old_json(json_file, run_range, version, pass_no):
    '''Update old documents to be more ratDB compatible
    :param: A dictionary representing a version_0 .json mapping file
    :retruns: An updated - rat compatible - dictionary.
    '''
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
    del json_file['_id']
    del json_file['_rev']
    json_file['index'] = ''
    json_file['comment'] = ''
    json_file['version'] = version
    json_file['run_range'] = run_range
    json_file['pass'] = pass_no
    json_file['timestamp'] = timestamp
    json_file['production'] = True
    json_file['last_valid'] = run_range[1]
    return json_file


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-p', dest='path',
                      default='./default_database/mapping/',
                      help='Path to ./default_database/mapping/ direc')
    parser.add_option('-v', dest='version', default=0,
                      help='Version of the calibration file type to be created - 0 by default')
    parser.add_option('--pass', dest='pass_no', default=1,
                      help='Pass number of file - 1 by default')
    (options,args) = parser.parse_args()
    pass_no = int(options.pass_no)
    version = int(options.version)
    if version > 0: 
        print 'This script has been written to update to the specific ratdb compatible' 
        print 'format as of Sept 2015. A new function will have to be written for any' 
        print 'newer revisions to the ratdb compatibility requirements.'

    # Check directory structure....
    # Check version dir exists
    path_to_version = check_dir('%sversion_%i/' % (options.path, version))
    save_path = check_dir('%spass_%i/' % (path_to_version, pass_no))

    # Read in old files and update
    if version == 0:
        old_files = os.listdir('%s/version_0/pass_0/' % (options.path))
        for file in old_files:
            run_range = []
            if file == 'map_Dec2014.js':
                run_range = [8715, 9100]
            elif file == 'map_March2014.js':
                run_range = [6968, 7225]
            elif file == 'map_Feb2014.js':
                run_range = [6241, 6802]
            file_path = '%s/version_0/pass_0/%s' % (options.path, file)
            json_dict = load_json(file_path)
            updated_dict = ratify_old_json(json_dict, run_range, version, pass_no)
            with open('%s%s' % (save_path, file), 'w+') as json_file:
                print 'Creating %s%s' % (save_path, file)
                json_file.write(json.dumps(updated_dict))
                json_file.close()
    print 'Converted all files from %s/version_0/pass_0/' % (options.path)
