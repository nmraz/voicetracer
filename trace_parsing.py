#!/usr/bin/python

def succeeded(ret_err):
    '''Returns a string describing the function's success/failure,
    based on its return value and errno
    '''
    ret_err = ret_err.split(' ', 1)
    try:
        ret = int(ret_err[0])
    except ValueError:
        return 'succeded'  # just assume success if the return value isn't integral
    if ret != -1:
        return 'succeded'
    return ('failed with error {}'.format(ret_err[1]) if len(ret_err) == 2
        else 'failed with unknon error')

def fmt_trace_line(line, db):
    '''Parses the line from the trace, and formats it according to the appropriate entry in `db`'''
    # NOTE: this is horrendously broken and should be replaced with a real parse!!!
    fn_start = line.find('(')
    if fn_start == -1:
        return  # some other message (not a function call)
    name = line[:fn_start]
    fmt = db.lookup(name)
    if not fmt:
        return
    rest = line[fn_start + 1:]
    fn_end = rest.find(')')  # end of the call
    args = map(lambda x: x.strip(),
        rest[:fn_end].split(','))
    eq_pos = rest[fn_end:].find('=')
    ret = rest[fn_end + eq_pos + 1:].strip()  # return value is after the `=` sign
    # format [arg1, arg2, ..., argN, ret], {succeeded} into the string
    return fmt.format(*(args + [ret]), succeeded = succeeded(ret))
