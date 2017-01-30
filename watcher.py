#!/usr/bin/python

import os
import threading
import time
from db_handler import DBHandler

class Watcher(object):
    '''Watches a trace file and speaks whenever a known systcall is encountered'''
    def __init__(self, db_path, trace_path):
        '''Initializes with the given trace file and database'''
        self.db = DBHandler(db_path)
        self.trace = open(trace_path, 'r')
        self.thr = threading.Thread(target = lambda: self.run())

        self.should_quit = False
        self.quit_lock = threading.Lock()  # protects `should_quit`

    def __enter__(self):
        '''Starts the watcher thread'''
        self.thr.start()

    def __exit__(self, exc_type, exc, trace):
        '''Requests the watcher to quit and frees its resources'''
        with self.quit_lock:
            self.should_quit = True
        self.thr.join()  # wait first to prevent concurrent access to resources
        self.trace.close()
        self.db.__exit__(exc_type, exc, trace)

    def run(self):
        '''The actual thread callback'''
        while True:
            new_line = self.trace.readline()
            if new_line:
                print new_line  # TODO: handle new message here
            else:
                with self.quit_lock:
                    if self.should_quit:
                        return
                time.sleep(0.0001)  # yield execution to another thread
