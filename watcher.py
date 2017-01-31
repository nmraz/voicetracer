#!/usr/bin/python

from db_handler import DBHandler
from trace_parsing import fmt_trace_line
import subprocess
import threading
import time

class Watcher(object):
    '''Watches a trace file and speaks whenever a known systcall is encountered'''
    def __init__(self, db_path, trace_path):
        '''Initializes with the given trace file and database'''
        self.db_path = db_path
        self.trace_path = trace_path
        self.thr = threading.Thread(target = lambda: self.run())

        self.should_quit = False
        self.quit_lock = threading.Lock()  # protects `should_quit`

    def __enter__(self):
        '''Starts the watcher thread and creates resources'''
        self.thr.start()

    def __exit__(self, exc_type, exc, trace):
        '''Requests the watcher to quit and frees its resources'''
        with self.quit_lock:
            self.should_quit = True
        self.thr.join()

    def run(self):
        '''The actual thread callback'''
        db = DBHandler(self.db_path)
        trace = open(self.trace_path, 'r')
        with trace, db:
            while True:
                new_line = trace.readline()
                if new_line:
                    msg = fmt_trace_line(new_line, db)
                    if msg:
                        subprocess.call(['espeak', '{}'.format(msg)])
                else:
                    with self.quit_lock:
                        if self.should_quit:
                            return
                    time.sleep(0.0001)  # yield execution to another thread
