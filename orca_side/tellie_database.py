#!/usr/bin/env python

# tellie_database.py
#
# TellieDatabase
#
# Author: Matt Mottram
#         (m.mottram@sussex.ac.uk)
#
# History:
#
###########################################
###########################################

import couchdb
import getpass


class TellieDatabase:
    """Class for all TELLIE - CouchDB calls.
    Will be replaced by whatever Orca uses.
    """

    #singleton instance - probably not pythonic, but I don't care
    _instance = None

    class SingletonHelper:

        def __call__(self, *args, **kw):
            if TellieDatabase._instance is None:
                object = TellieDatabase()
                TellieDatabase._instance = object
            return TellieDatabase._instance

    get_instance = SingletonHelper()

    def __init__(self):
        self.db = None
        self.host = None
        self.name = None

    def login(self, host, name):
        self.host = host
        self.name = name
        print self.host
        print self.name
        couch = couchdb.Server(self.host)
        try:
            self.db = couch[self.name]
        except:
            user = raw_input("DB Authentication, username: ")
            password = getpass.getpass("DB Authentication, password: ")            
            couch.resource.credentials = (user, password)
            self.db = couch[self.name]

    def is_logged_in(self):
        if self.db is None:
            return False
        return True

    def save(self, doc):
        self.db.save(doc)
