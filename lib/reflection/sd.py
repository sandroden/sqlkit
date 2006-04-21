"""some useful functions..."""

import sys, re

def debug(*text):
    if dbg==0:
        return
    print "%s: %s" % (caller(), text)

def caller():
    frame = sys._getframe(2)
    caller = frame.f_code.co_name
    class_name = ''
    try:
        a = frame.f_locals['self'].__class__
        class_name =  re.search("'(.*)'", str(a)).group(1) + "."
    except:
        pass
    return "%s%s" % (class_name, caller)
    
def dshow(diz, filter=None):
    if dbg==0:
        return

    print caller()
    for k,v in diz.iteritems():
        if filter:
            if not re.search(filter, k):
                continue
        print "    ", k, v

