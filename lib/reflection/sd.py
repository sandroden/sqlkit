"""some useful functions..."""

import sys, re

def debug(*text):
    if dbg==0:
        return
    if not text:
        text = caller(mode='loc')

    txt = ""
    for i in text:
        txt += " " + str(i)
    print "%s: %s" % (caller(), txt)

def caller(mode=None):
    frame = sys._getframe(2)
    caller = frame.f_code.co_name
    class_name = ''

    if mode == 'loc':
        return frame.f_locals
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


def sql_debug(sql, params):
    dbg = re.sub(':(?P<a>\S+)', '\'%(\g<a>)s\'', sql)
    #sd.debug("%s %s" % (dbg, params))
    debug(dbg % params)
