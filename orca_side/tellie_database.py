#!/usr/bin/env python
# tellie_database.py
#
# TellieDatabase
#
# Author: Matt Mottram
#         (m.mottram@sussex.ac.uk)
#
# History:
#         Major revisions and additions (19/05/16)
#         <e.leming@sussex.ac.uk>
#
###########################################
###########################################

import couchdb
import getpass


class TellieDatabase:
    """Class for all TELLIE - CouchDB calls.
    Will be replaced by whatever Orca uses.
    """

    def __init__(self, host, database, username=None, password=None):
        self.host = host
        self.username = username
        self.database = database
        couch = couchdb.Server(self.host)
        if username is not None and password is not None:
            couch.resource.credentials = (username, password)
        try:
            self.db = couch[self.database]
        except:
            username = raw_input("DB Authentication, username: ")
            password = getpass.getpass("DB Authentication, password: ")            
            couch.resource.credentials = (username, password)
            self.db = couch[self.database]

    def is_logged_in(self):
        if self.db is None:
            return False
        return True
    
    def save(self, doc):
        return self.db.save(doc)

    def get_view(self, view_name, keys=None, ascending=True, include_docs=False):
        '''Return view object'''
        if keys == None:
            return self.db.view(view_name, ascending=ascending, include_docs=include_docs)
        else:
            return self.db.view(view_name, keys=keys, ascending=acsending, include_docs=include_docs)

    def load_doc(self, doc_id):
        '''Return specific doc from db
        '''
        return self.db.get(doc_id)

    def get_docs_from_view(self, view_name):
        '''Get all docs returned by a view
        '''
        rows = self.get_view(view_name, include_docs=True)
        return [row.doc for row in rows]

    def update_doc(self, doc_id, update_fields):
        '''Update document of type _id with fields in update_fields
        '''
        old_doc = self.load_doc(doc_id)
        new_doc = {}
        for key in old_doc.keys():
            if key in update_fields:
                new_doc[key] = update_fields[key]
            else:
                new_doc[key] = old_doc[key]
        self.save(new_doc)
