#!/usr/bin/python

from watcher import Watcher
import subprocess
import random
import string

def gen_trace_path():
    '''Generates a (relatively) random name for the temporary trace file, to reduce the
    likelihood of collision between multiple running instances of voicetracer
    '''
    # genrate a string of 10 random letters/digits
    rand_part = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(10)])
    return '/tmp/voice-trace-{}.log'.format(rand_part)

def voicetrace(cmd, db_path):
    '''Main function: runs `cmd` and verbally traces its system calls using descriptions provided
    in the database located at `db_path`
    '''
    trace_path = gen_trace_path()
    open(trace_path, 'w+').close()  # ensure that the file exists before starting the watcher
    with Watcher(db_path, trace_path):
        subprocess.call(['strace', '-o', trace_path, '--'] + cmd.split())
