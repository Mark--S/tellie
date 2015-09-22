#########################################
# Script to upload static channel files
# to cauch.db
#
# Author: e.leming@sussex.ac.uk
#########################################
import json
import couchdb
import optparse
import os

def jsons_to_dict(path):
    '''Get a list of paths to all json files.
    '''
    files = os.listdir(path)
    dicts = []
    for f in files:
        dicts.append(json.loads(open("%s/%s" % (path, f)).read()))
    return dicts

def connect_to_telliedb():
    server = couchdb.Server("http://couch.snopl.us")
    return server["telliedb"]

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-p", dest="path", default="./default_database/channels_new")
    (options,args) = parser.parse_args()    

    json_files = get_json_list(options.path)
    database = connect_to_telliedb()
    for f in json_files:
        database.save(f)
