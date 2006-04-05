"""some useful functions..."""

import sys

def debug(text):
    if dbg==0:
        return
    caller = sys._getframe(1).f_code.co_name
    print "%s: %s" % (caller, text)
