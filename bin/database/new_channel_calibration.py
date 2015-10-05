'''Module to add a new set of channel calibration files. This is a work in 
progress as new functions should be written and included here if there 
is a version change in the channel calibration db file format.

Author: Ed Leming <e.leming@sussex.ac.uk>
'''

import json
import os
import optparse
import csv
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

def get_int_from_string(string):
    '''Quick function to return integers from string
    '''
    ints = ''.join(x for x in string if x.isdigit())
    return int(ints)

def load_jsons_from_direc(path): 
    '''Load all json files from the passed directory
    :param: Path .json directory.
    :returns: List of dictionary objects representing the .jsons.
    '''
    data_list = []
    files = os.listdir(path)
    for file in files:
        with open('%s/%s' % (path, file), 'r') as json_file:
            json_data = json.load(json_file)
            data_list.append(json_data)
    return data_list

def get_channel_fit_pars(fname):
    '''Read in data from csv file containing all channels results and return a dict
    of the photonVsIPW fit parameters.
    '''
    pars_dict = {}
    results = csv.DictReader(open(fname))
    for idx, line in enumerate(results):
        pars_dict[line['channel']] = ([float(line['ipw_p0']), float(line['ipw_p1']),
                                       float(line['ipw_p2'])])
    return pars_dict

def ratify_original_calibrations(json_list, run_range, pass_no):
    '''Add run number and comment fields to original calibration files.
    these will be saved with an updated pass filed, but not version (as they're 
    essentially the same!)
    '''
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
    for json_file in json_list:
        json_file['channel'] = json_file['index']
        json_file['index'] = ''
        json_file['comment'] = ''
        json_file['run_range'] = run_range
        json_file['pass'] = pass_no
        json_file['timestamp'] = timestamp
        json_file['production'] = True
    return json_list

def update_v1_calbration(fname, json_list, run_range, pass_no):
    '''Replace old photon-IPW lookup table with parameters from fits to the
    calibrated response curves. Need to include fields for both 10Hz and 1kHz
    calibrations.
    '''
    timestamp = datetime.datetime.now(pytz.timezone('US/Eastern')).isoformat()
    pars = get_channel_fit_pars(fname)
    for json_file in json_list:
        # Channel 96 does not exist at site
        if json_file['index'] == 96:
            json_list.remove(json_file)
            continue
        else:
            # Delete old fields and update
            del json_file['photons']
            del json_file['pulse_width']
            json_file['channel'] = json_file['index']
            json_file['index'] = ''
            json_file['comment'] = ''
            json_file['run_range'] = run_range
            json_file['pass'] = pass_no
            json_file['Pars_10Hz'] = [0, 0, 0]
            json_file['Eq_10Hz'] = 'poly2'
            json_file['Pars_1kHz'] = pars['%i' % json_file['channel']]
            json_file['Eq_1kHz'] = 'poly2'
            json_file['version'] = 1
            json_file['timestamp'] = timestamp
            json_file['production'] = True
    return json_list
        
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-p', dest='path',
                      default='./default_database/channels/',
                      help='Path to ./default_database/channels/ direc')
    parser.add_option('-c', dest='calibration',
                      help='Path to current calibration data direc')
    parser.add_option('-v', dest='version', default=1,
                      help='Version of the calibration file type to be created')
    #parser.add_option('-r', dest='run_valid',
    #                 help='The run from which the new calibrations become valid'
    (options,args) = parser.parse_args()
    version = int(options.version)
    if version > 0 and not options.calibration:
        parser.error('You must include a path to calibration files to be read')

    # Check directory structure....
    # Check version dir exists
    path_to_version = '%sversion_%i/' % (options.path, version)
    check_dir(path_to_version)
    # Find last pass in this version
    last_pass = -1
    passes = os.listdir(path_to_version)
    for ent in passes:
        if get_int_from_string(ent) > last_pass:
            last_pass = get_int_from_string(ent)
    pass_no = last_pass + 1
    save_path = check_dir('%spass_%i/' % (path_to_version, pass_no))
    
    # Depending on version number, create new files
    original_calibs = load_jsons_from_direc('%sversion_0/pass_0/' % options.path)
    if version == 0:
        run_range = [0, 9435] # Last run at time of writing this script
        new_json_list = ratify_original_calibrations(original_calibs, run_range,
                                                         pass_no)
    elif version == 1:
        run_range = [9436, 0]
        new_json_list = update_v1_calbration(options.calibration, original_calibs, 
                                             run_range, pass_no)
    else:
        print 'No conversion fucntion exists for version = %i' % version
        raise ValueError('You\'re going to have to write a new function!')
    
    # Save to file
    for data_dict in original_calibs:
        with open('%sch%03d.js' % (save_path, int(data_dict['channel'])), 'w+') as json_file:
            json_file.write(json.dumps(data_dict))
            json_file.close()
    print 'New calibration files saved to: %s' % save_path
