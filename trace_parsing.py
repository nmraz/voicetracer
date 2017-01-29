#!/usr/bin/python

def fmt_trace_line(line, db):
    '''Parses the line from the trace, and formats it according to the appropriate entry in `db`'''
    # TODO: do a real parse here, not just a bunch of splits
    # (simple splitting doesn't play nicely with string literals)
    fn_start = line.find('(')
    if fn_start == -1:
        return  # some other message (not a function call)
    name = line[:fn_start]
    fmt = db.lookup(name)
    if not fmt:
        return
    rest = line[fn_start + 1:]
    fn_end = rest.find(')')  # end of the call
    args = map(lambda x: x.strip(), rest[:fn_end].split(','))
    eq_pos = rest[fn_end:].find('=')
    ret = rest[fn_end + eq_pos + 1:].strip()  # return value is after the `=` sign
    return fmt.format(*(args + [ret]))  # format [arg1, arg2, ..., argN, ret] into the string
