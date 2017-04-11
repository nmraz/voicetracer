#!/usr/bin/python

import os
import subprocess
import threading
import time

from db_handler import DBHandler
from trace_parsing import fmt_trace_line


class Watcher(object):
    """Watches a trace file and speaks whenever a known systcall is
    encountered
    """

    def __init__(self, db_path, trace_path):
        """Initializes with the given trace file and database"""
        self.db_path = db_path
        self.trace_path = trace_path
        self.thr = threading.Thread(target = lambda: self.run())

        # 0 = don't quit, 1 = quit when done, 2 = quit now
        self.should_quit = 0
        self.quit_lock = threading.Lock()  # protects `should_quit`

    def __enter__(self):
        """Starts the watcher thread and creates resources"""
        self.thr.start()

    def __exit__(self, exc_type, exc, trace):
        """Requests the watcher to quit and frees its resources"""
        with self.quit_lock:
            self.should_quit = 2 if exc_type else 1
        try:
            # workaround to allow KeyboardInterrupt during join
            while self.thr.is_alive():
                self.thr.join(0.0001)
        except:
            with self.quit_lock:
                self.should_quit = 2

    def run(self):
        """The actual thread callback"""
        db = DBHandler(self.db_path)
        trace = open(self.trace_path, 'r')
        with trace, db:
            while True:
                with self.quit_lock:
                    should_quit = self.should_quit
                if should_quit == 2:  # quit now
                    return

                new_line = trace.readline()
                if new_line:
                    msg = fmt_trace_line(new_line, db)
                    if msg:
                        subprocess.call(['espeak', msg],
                            preexec_fn = lambda: os.setpgrp())
                else:
                    if should_quit:
                        return
                    time.sleep(0.0001)  # yield execution to another thread
