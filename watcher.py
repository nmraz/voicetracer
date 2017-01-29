#!/usr/bin/python

import os
import threading
from db_handler import DBHandler

class Watcher(object):
    '''Watches a trace file and speaks whenever a known systcall is encountered'''
    def __init__(self, db_path, trace_path):
        '''Initializes with the given trace file and database'''
        self.db = DBHandler(db_path)
        self.trace = open(trace_path)
        self.thr = threading.Thread(target = lambda: self.run())

    def __enter__(self):
        '''Starts the watcher thread'''
        self.thr.start()

    def __exit__(self, exc_type, exc, trace):
        self.thr.join()  # wait first to prevent concurrent access to resources
        self.trace.close()
        self.db.__exit__(exc_type, exc, trace)

    def run(self):
        '''The actual thread callback'''
        for line in self.trace:
            pass  # TODO: implement trace parsing/speaking
