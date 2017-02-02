#!/usr/bin/python
"""This module defines handlers for system calls which need special
treatment. Each handler has the ability to prevent a system call from
being traced, as well as to add additional named arguments to the format
string.
"""

_open_sockets = {}

def on_socket(args, ret, err, additional_args):
    """Called whenever a call to `socket` is encountered. This function
    adds the file descriptor of the socket to the list of open sockets
    """
    if ret != '-1':
        _open_sockets[ret] = True
    return True  # always trace this call

def on_close(args, ret, err, additional_args):
    """Called whenever a call to `close` is encountered. If the call
    closes a socket, this function allows it to be traced and removes
    its file descriptor from the list of open sockets; otherwise, the
    call is ignored.
    """
    fd = args[0].val
    if ret != '-1' and fd in _open_sockets:
        del _open_sockets[fd]
        additional_args['type'] = 'socket'
        return True
    return False

handlers = {
    'socket': on_socket,
    'close': on_close
}
