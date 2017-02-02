#!/usr/bin/python

import re

from special_handlers import handlers


class Stream(object):
    """Represents a character stream and a token position inside it"""

    def __init__(self, str, pos = 0, start = 0):
        """Initializes the stream with `str` and sets its token start
        and end to 0
        """
        self.str = str
        self.pos = pos
        self.start = start

    def peek(self):
        """Returns the next character"""
        if not self.eof():
            return self.str[self.pos]

    def next(self):
        """Advances the stream and returns the next character, if possible"""
        next = self.peek()
        self.pos += 1
        return next

    def eat(self, chs):
        """If the next character is one of `chs`, advances the stream
        and returns True; returns False otherwise
        """
        if re.search('[{}]'.format(chs), self.peek() or ''):
            self.next()
            return True
        return False

    def eat_while(self, chs):
        """Advances the stream until a character which isn't one of
        `chs` is encountered
        """
        while self.eat(chs):
            pass

    def eat_tok(self, ch):
        """Attempts to consume `ch` as a unique token"""
        self.newtok()
        consumed = self.eat(ch)
        self.newtok()
        return consumed

    def eof(self):
        """Returns whether the token pos is at the end of the stream"""
        return self.pos >= len(self.str)

    def newtok(self):
        """Skips any whitespace and sets the token start to the current
        position, starting a new token
        """
        self.eat_while('\s')
        self.start = self.pos

    def curtok(self):
        """Returns the current token"""
        return self.str[self.start:self.pos]


class Val(object):
    """An object which may be used as either a string, a dictionary, or
    a list. These qualities make it easy to format the object into
    format strings expecting objects with various characteristics.
    """

    def __init__(self, val = None):
        """Initializes with the given value and type"""
        self.val = val

    def __getitem__(self, key):
        """Behave like a list or a dictionary"""
        if ((type(self.val) is list and 0 <= key < len(self.val))
            or (type(self.val) is dict and key in self.val)):
            return self.val[key]
        return Val()  # allow for recursive operations

    def __str__(self):
        """Behave like a string (simply return string representation of
        underlying object)
        """
        if type(self.val) is dict:
            # recursively stringify dictionary
            return str({key: str(val) for key, val in self.val.iteritems()})
        elif type(self.val) is list:
            # recursively stringify list
            return str([str(item) for item in self.val])
        else:
            return str(self.val)


# The following functions implement a recursive-descent parser for the
# c-like syntax which strace uses, with one caveat: expressions are not
# parsed fully. This may, on rare occasions, lead to misinterpretation
# of the string, although it is much better than having no parser at all.

def eat_string(stream):
    """Advances the stream to the end of the string, respecting escape
    sequences
    """
    escaped = False  # are we in an escape sequence?
    ch = stream.next()
    while ch is not None:
        if ch == '"' and not escaped: break  # end of string
        # every backslash toggles "escapiness"
        escaped = ch == '\\' and not escaped
        ch = stream.next()

def parse_array(stream, term):
    """Parses an array terminated by `term`, and returns a list of the
    elements
    """
    ret = []
    if not stream.eat_tok(term):  # non-emptiness check
        ret.append(parse_expr(stream, ',' + term))
        while stream.eat_tok(','):  # comma-separated
            ret.append(parse_expr(stream, ',' + term))
    stream.eat_tok(term)
    return ret

def parse_struct_field(stream):
    """Parses something of the form 'name=expr' and returns a tuple
    (name, expr) or None on failure
    """
    stream.newtok()
    stream.eat_while('\w')  # identifier
    name = stream.curtok()
    if not stream.eat_tok('='):
        return None
    expr = parse_expr(stream, ',}')  # use ',}' as sync tokens
    return (name, expr)

def parse_struct(stream):
    """Parses a c-struct-like construct and returns an dictionary Val"""
    # e.g. '{a=1, b=2}' => Val({'a': 1, 'b': 2})
    ret = {}
    if not stream.eat_tok('}'):  # non-emptiness check
        name, expr = parse_struct_field(stream)
        ret[name] = expr
        while stream.eat_tok(','):
            data = parse_struct_field(stream)
            if not data:  # an unnamed field within a struct?
                stream.eat_while('^,}')  # jump to nearest sync token
                continue
            ret[data[0]] = data[1]
    stream.eat_tok('}')
    return Val(ret)

def parse_expr(stream, terms):
    """Attempts to parse an expression, and jumps to one of `terms` at
    the end/at failure. Returns a Val representing what it parsed
    (e.g. a struct, array, string)
    """
    ret = Val()
    stream.newtok()
    if stream.eat('"'):  # start of string
        eat_string(stream)
        ret = Val(stream.curtok())
    elif stream.eat_tok('['):  # start of array
        ret = Val(parse_array(stream, '\]'))
    elif stream.eat_tok('{'):  # either struct OR array
        tmp_stream = Stream(stream.str, stream.pos, stream.start)
        if parse_struct_field(tmp_stream):
            ret = parse_struct(stream)
        else:
            # this can happen in select, for example
            ret = Val(parse_array(stream, '}'))
    else:
        stream.eat_while('^(' + terms)  # not a very good parse
        name = stream.curtok().strip()
        if stream.eat_tok('('):
            # function call: return [name, arg1, arg2, ...]
            ret = Val([name] + parse_array(stream, ')'))
        else:
            # give up...
            ret = Val(name)
    stream.eat_while('^' + terms)
    return ret

def parse_sys_call(stream):
    """Parses to the end of the system call, and returns (args, ret, err),
    where args is a list of the arguments, ret is the return value,
    and err is the description following it
    """
    args = parse_array(stream, ')')
    if not stream.eat_tok('='):
        return (args, None, None)
    stream.eat_while('\S')
    ret = stream.curtok()
    stream.newtok()
    stream.pos = len(stream.str)  # just take everything at this point
    err = stream.curtok()
    return (args, ret, err)


def succeeded(ret, err):
    """Returns a string describing the function's success/failure,
    based on its return value and errno
    """
    if ret == '-1':
        return 'failed with error {}'.format(err) if err else 'failed'
    else:
        return 'succeeded with {}'.format(err) if err else 'succeeded'


def fmt_trace_line(line, db):
    """Parses the line from the trace, and formats it according to the
    appropriate entry in `db`
    """
    stream = Stream(line)
    stream.eat_while('\w')
    name = stream.curtok()
    if not stream.eat_tok('('):  # not a function call
        return
    fmt = db.lookup(name)
    if not fmt and not name in handlers:  # nothing to do
        return
    additional_args = {}
    args, ret, err = parse_sys_call(stream)
    if name in handlers:
        if not handlers[name](args, ret, err, additional_args):
            # the handler bailed out
            return
    return fmt.format(*args, ret = ret, succeeded = succeeded(ret, err),
                      **additional_args)
