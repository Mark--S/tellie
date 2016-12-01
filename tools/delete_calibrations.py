################################################
# A quick script to delete any docs mistakenly
# uploaded to telliedb
#
# Author: Ed Leming <e.leming@sussex.ac.uk>
#
################################################
from orca_side import tellie_database
import couchdb
import csv
import datetime
import pytz
import argparse
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server', help='database server [http://couch.snopl.us]',
                      default='http://couch.snopl.us')
    parser.add_argument('-d', dest='database', help='database name [telliedb]',
                      default='telliedb')
    args = parser.parse_args()

    # Get reference to the tellie database
    db = tellie_database.TellieDatabase(args.server, args.database)

    current_docs = []
    all_docs = db.get_docs_from_view("_design/channels/_view/channel_by_number")
    for doc in all_docs:
        if doc["run_range"][1] == 10416:
            db.delete(doc)
