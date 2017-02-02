#!/usr/bin/python

import sqlite3 as sql


class DBHandler(object):
    """Holds a database connection and allows for descriptions to be
    found for corresponding syscall names
    """

    def __init__(self, path):
        """Initializes the connection with the database specified by `path`"""
        self.con = sql.connect(path)

    def __enter__(self):
        pass  # nothing to do here...

    def __exit__(self, exc_type, exc, trace):
        """Cleans up resources (the database connection)"""
        self.con.close()

    def lookup(self, name):
        """Looks up the specified syscall in the database and returns
        its description, if any
        """
        cur = self.con.cursor()
        cur.execute("SELECT description FROM tab WHERE name='{}'".format(name))
        row = cur.fetchone()  # there shouldn't be more than one entry anyway
        if row:
            return row[0]
        return ''
