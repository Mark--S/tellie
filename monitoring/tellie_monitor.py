import os
import sys
import subprocess
import string
import optparse
import numpy
import time
import calendar
from orca_side import tellie_database


class Vector():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    @classmethod
    def from_r_theta_phi(cls, r, theta, phi):
        x = r * numpy.cos(phi) * numpy.sin(theta)
        y = r * numpy.sin(phi) * numpy.sin(theta)
        z = r * numpy.cos(theta)
        return cls(x, y, z)
    def set_xyz(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def set_r_theta_phi(self, r, theta, phi):
        self.x = r * numpy.cos(phi) * numpy.sin(theta)
        self.y = r * numpy.sin(phi) * numpy.sin(theta)
        self.z = r * numpy.cos(theta)
    def dot(self, v):
        return self.x * v.x + self.y * v.y + self.z * v.z


def run_rat(template_name, macro_name, input_name, output_name):
    '''Write RAT macro and analyse TELLIE run
    '''
    template = string.Template(open(template_name, 'r').read())
    macro_text = template.substitute(INPUT = input_name,
                                     OUTPUT = output_name)
    macro = file(macro_name, 'w')
    macro.write(macro_text)
    macro.close()
    os.system('rat -l tellie.log %s' % macro_name)
    os.unlink(macro_name)


def get_expected_hits(filename):
    '''Get the phi/theta of direct and reflected spots
    '''
    fin = file(filename, 'r')
    direct_vectors = {}
    reflected_vectors = {}
    for line in fin.readlines():
        bits = line.split()
        if len(bits)!=5:
            continue
        fibre = bits[0][6:-5]
        fibre_number = int(fibre[:-1])
        fibre = "%d%s" % (fibre_number, fibre[-1])
        direct_phi = float(bits[1])
        direct_theta = float(bits[2])
        reflected_phi = float(bits[3])
        reflected_theta = float(bits[4])
        direct_vectors[fibre] = Vector.from_r_theta_phi(1, direct_phi, direct_theta)
        reflected_vectors[fibre] = Vector.from_r_theta_phi(1, reflected_phi, reflected_theta)
    return direct_vectors, reflected_vectors


def check_fibre(direct_vectors, output_name, mapping, channel_selected, output_log):
    '''Check the output angles from processed job to expected from simulation.
   
    Compares the best guess fibres to available fibres and the one selected by the GUI.
    '''
    fin = file(output_name, 'r')
    line = fin.readline()
    n_events = int(line.split()[-1])
    if n_events<100:
        print "CANNOT ANALYSE FILE: %s" % n_events
        return
    line = fin.readline()
    direct_phi = float(line.split()[1])
    direct_theta = float(line.split()[2])
    reflected_phi = float(line.split()[1])
    reflected_theta = float(line.split()[2])
    run_direct_vector = Vector.from_r_theta_phi(1, direct_phi, direct_theta)
    run_reflected_vector = Vector.from_r_theta_phi(1, reflected_phi, reflected_theta)
    dot_product_list = []
    fibre_list = []

    for fibre in direct_vectors:
        dot_product = run_direct_vector.dot(direct_vectors[fibre])
        dot_product_list.append(dot_product)
        fibre_list.append(fibre)

    # Find the best *connected* fibre
    mapping_index = mapping['channels'].index(channel_selected)
    fibre_selected = mapping['fibres'][mapping_index]
    dot_selected = dot_product_list[fibre_list.index(fibre_selected)]
    n_check = len(dot_product_list)
    for i in range(n_check):
        max_index = dot_product_list.index(max(dot_product_list))
        max_dot = dot_product_list[max_index]
        max_fibre = fibre_list[max_index]
        if unicode(max_fibre) in mapping['fibres']:
            break
        # If here, the fibre was not connected...
        dot_product_list.pop(max_index)
        fibre_list.pop(max_index)

    print "BEST:     %s\t%s" % (max_fibre, max_dot)
    print "SELECTED: %s\t%s" % (fibre_selected, dot_selected)
    output_file = file(output_log, 'w')
    output_file.write("BEST\t%s\t%s\n" % (max_fibre, max_dot))
    output_file.write("SELECTED\t%s\t%s\n" % (fibre_selected, dot_selected))
    output_file.close()
                      

def run_from_zdab(input_name):
    '''Get a run number from SNOP_xxxx format name
    '''
    filename = os.path.basename(input_name)
    run = int(filename.split("_")[1])
    return run


def get_mapping_doc(database, timestamp):
    '''Get a mapping document for a given timestamp
    '''
    # Must get all rows (timestamp for mapping will be between runs)
    # But view is small, so should be fine.
    rows = database.db.view("_design/channels/_view/map_by_time", descending=True)
    doc = None
    for i, row in enumerate(rows):
        if row.key[0] < timestamp:
            # This is the first row with a time older than the run -> the correct mapping
            # (the descending will cover both timestamp and pass number)
            mapping_doc = database.db[row.id]
            return mapping_doc
    raise Exception("No mapping found for %s" % timestamp)


def get_run_timestamp(orca_database, run):
    '''Return a UNIX time format timestamp for the start of run.
    '''
    rows = orca_database.db.view('_design/snopldotus/_view/index', key=run, include_docs=True)
    if len(rows)!=1:
        raise Exception("Multiple run documents from OrcaDB!")
    for row in rows:
        run_start = str(row.doc['run_start']) #.replace("T", " ").replace("Z", " ")
        # Interpret timestamp format (not UNIX time atm), assume at least UTC
        run_start = time.strptime(run_start, "%Y-%m-%dT%H:%M:%S.%fZ") # time doesn't account for fractions, I don't care
        run_timestamp = calendar.timegm(run_start)
    return run_timestamp


def get_tellie_channel(database, run):
    '''Get the channel fired for a given run.
    '''
    rows = database.db.view('_design/runs/_view/run_by_number', key=run, include_docs=True)
    channel = None
    for row in rows:
        channels = row.doc['fire_settings']['channels']
        if len(channels)!=1:
            raise Exception("Cannot handle >1 channel")
        if channel is None:
            channel = channels[0]
        elif channels[0] != channel:
            raise Exception("Multiple channels fired for this run; cannot monitor")
    if channel is None:
        print "No TELLIE events for run %s" % run
        return None
    return int(channel)


if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', dest='input_name', help='file to monitor')
    parser.add_option('-o', dest='output_name', help='tellie monitor file to create')
    parser.add_option('-r', dest='run', help='run number (taken from input file name if not set)', default=None)
    parser.add_option('-t', dest='template_name', help='template tellie macro', default='procTellie.mac')
    parser.add_option('-m', dest='macro_name', help='macro to create and run', default='tellie.mac')
    parser.add_option('-a', dest='angles_name', help='list of expected central direct/refl hits', default='angles.dat')
    parser.add_option('-s', dest='database_server', help='TELLIE database server [http://couch.ug.snopl.us]', default='http://couch.ug.snopl.us')
    parser.add_option('-n', dest='database_tellie', help='TELLIE database name [tellie]', default='tellie')
    parser.add_option('-c', dest='database_orca', help='Orca database name [orca]', default='orca')
    parser.add_option('-u', dest='database_user', help='TELLIE database user [snoplus]', default='snoplus')
    parser.add_option('-p', dest='database_password', help='TELLIE database password (remember to escape any special characters)', default=None)
    (options, args) = parser.parse_args()
    
    direct_vectors, reflected_vectors = get_expected_hits(options.angles_name)

    if options.run:
        run = int(options.run)
    else:
        run = run_from_zdab(options.input_name)

    # Get run level information from the tellie database
    # TODO: this might be better taken via a web monitor later.
    database = tellie_database.TellieDatabase()
    orca_database = tellie_database.TellieDatabase()
    database.login(options.database_server, options.database_tellie, options.database_user, options.database_password)
    orca_database.login(options.database_server, options.database_orca, options.database_user, options.database_password)

    channel = get_tellie_channel(database, run)
    if channel is None:
        # Don't need an abnormal exit code
        sys.exit()
    timestamp = get_run_timestamp(orca_database, run)
    mapping = get_mapping_doc(database, timestamp)

    print "channel", channel, timestamp

    if channel not in mapping['channels']:
        raise Exception("Channel %s is not in mapping document" % channel)

    run_rat(options.template_name, options.macro_name, options.input_name, options.output_name)
    
    if not os.path.exists(options.output_name):
        raise Exception("No output %s created" % options.output_name)

    # Can now check the number of triggers and central spot
    check_fibre(direct_vectors, options.output_name, mapping, channel, "%s.comp" % options.output_name)
