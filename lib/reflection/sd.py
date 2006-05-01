"""some useful functions..."""

import sys, re

def debug(filter=None, sfilter=None, *text):
    if dbg==0:
        return
    if not text:
        print "%s (%s): \n%s" % (caller(), caller(mode='lineno'),
                          dshow(caller(mode='loc', level=2),
                                filter=filter, sfilter=sfilter,mute=True) )
        return
    
    txt = ""
    for i in text:
        txt += " " + str(i)
    print "%s (%s): %s" % (caller(), caller(mode='lineno'), txt)

def caller(mode=None, level=2):
    frame = sys._getframe(level)

    if mode == 'lineno':
        return frame.f_lineno
    
    if mode == 'loc':
        return frame.f_locals

    caller = frame.f_code.co_name
    class_name = ''

    try:
        a = frame.f_locals['self'].__class__
        class_name =  re.search("'(.*)'", str(a)).group(1) + "."
    except:
        pass
    return "%s%s" % (class_name, caller)
    
def show_caller(filter=None, sfilter=None):
    print "%s called from: %s (%s) \n%s" % (
        caller(),
        caller(level=3), caller(level=3, mode='lineno'), 
        dshow(caller(mode='loc', level=3),
              filter=filter, sfilter=sfilter,mute=True) )

def dshow(diz, filter=None, sfilter=None, mute=False):
    if dbg==0:
        return

    txt = []
    if not mute:
        txt += [caller()]
    for k,v in diz.iteritems():
        if filter:
            if not re.search(filter, k):
                continue
        if sfilter:
            if re.search(sfilter, k):
                continue
        txt += ["    %s: %s" % (k, v)]
    return "\n".join(txt)


def sql_debug(sql, params):
    dbg = re.sub(':(?P<a>\S+)', '\'%(\g<a>)s\'', sql)
    #sd.debug("%s %s" % (dbg, params))
    debug(dbg % params)
