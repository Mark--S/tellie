from orca_side import tellie_database
import json


database = tellie_database.TellieDatabase.get_instance()
# Assume login is always the snopl machine for now
database.login('http://couch.snopl.us', 'tellie')


def get_run(run):
    '''Get results for a given run.

    Returns as a list (in case of multiple sequences per run.
    '''
    rows = database.db.view('_design/runs/_view/run_by_number', key=run,
                            include_docs=True)
    if len(rows)==0:
        print "No TELLIE data for run %s" % run
        return None
    elif len(rows)!=1:
        print "Multiple sequences fired for run %s" % run
    run_data = []
    for row in rows:
        run_data.append(row.doc)
    return run_data
