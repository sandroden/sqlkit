"""
This module provides easy way to debug with print commands. This may not be
the best way to debug, many times pdb will be much more powerfull. Nevertheless
I found mysel in need of these functions...

The way to use this is

  1. in you library::

     import dbg
     dbg.write('text message', 'text2')

  2. in you application::

     import dbg
     dbg.debug(True)

write() - caller()
------------------
     
from now on, each time you use dbg.write()/dbg.caller() you'll see the text you
want to log anly if you enabled it with dbg.debug(True)

If you want the log to happen in a gtk.TreeView window, you can specify:;

     import dbg
     dbg.debug(True, gtk=True)


Logging methods
---------------

Following recepe 198078 in the ASP Python CookBook (see in the code)
this module provides also a metaclass to trace the use of methods of a
particular class. It will be instantiated as::

   class A(object):
       __metaclass__ = dbg.LogTheMethods

for each method call a line will be logged (unless configured to be ignored)
with

    function called
    caller class
    arguments
    caller function
    line of code
    return code
    calling class
    time elapsed

IMPORTANT: since the logging occurs with metaclasses you need to import dbg and
           set debugging *before* importing the class you want to trace::

    import dbg
    dbg.debug(True, gtk=True)
    dbg.trace_class('SqlTable2')  # optional
    dbg.trace_function(exclude='cell_default_cb|cell_bool_cb')  # optional
    import sqlkit

TraceIt
-------

in case you need to understand who is changeing the value of a variable, you
can use TraceIt as::

    commit_allowed = dbg.TraceIt(True, name='commit_allowed', mode='rw')

and use it as a normal variable.  You'll get lines in your output stating
who changed the value of that variable, in the form::

     __str__/function_name:  old_value => new_value
     __get__/function_name:  value

  
"""

import sys, re
import new
import layout, pango, inspect
import tokenize
import keyword
import time
import inspect
from  pdb import set_trace

CLASS_INCLUDE = '^.*$'
CLASS_EXCLUDE = '^$'
FUNCTION_INCLUDE = re.compile('.*')
FUNCTION_EXCLUDE = re.compile('^$')

class FakeLogger(object):
    def add(self, *args,**kw):
        pass
    def write(self, *args, **kw):
         write(*args, **kw)
    def ret(self, iter, value):
        return value

DBGLogger = FakeLogger()
#DBGLogger = None
DBG = False

def test():
    global DBG
    print "DBG:", DBG
    
def debug(x=None, gtk=False):
    global DBGLogger
    global DBG
    
    if gtk == True:
        DBGLogger = ShowLogs(show=True)

    if x is True:
        DBG = 1
    if x is False:
        DBG = 0
    if isinstance(x , int):
        DBG = x

    
def write(*text, **kwargs):
    global DBG
    global DBGLogger
    if 'filter' not in kwargs:
        filter = None
    
    if 'sfilter' not in kwargs:
        sfilter = None
    
    if 'direct' not in kwargs:
        kwargs['direct'] = False

    if 'meth' not in kwargs:
        meth = caller()
    else:
        meth = kwargs['meth']
        
    if 'called_by' not in kwargs:
        called_by = ''
    else:
        called_by = kwargs['called_by']
        
    if DBG == 0:
        return
    if not text:
        ### FIXME: should go to DBGLogger...?
        print "%s (line %s) locals(): \n%s" % (caller(), caller(mode='lineno'),
                          dshow(caller(mode='loc', level=2), ret=True,
                                filter=filter, sfilter=sfilter,mute=True))
                                               
        return
    
    txt = ""
    for i in text:
        txt += " " + str(i)

    if not kwargs['direct'] and DBGLogger:
        try:
            instance=caller(mode='instance')
            Class_str = instance.nick
        except Exception, e:
            Class_str = ''
        
        DBGLogger.write(txt=txt, line=caller(mode='lineno'), meth=meth,
                        mode='write', Class=Class_str, caller=called_by)
    else:
        #print "dbg.write: QUI 2, DBGLogger:", DBGLogger, "direct:", kwargs['direct']
        print "%s (line %s): %s" % (caller(), caller(mode='lineno'), txt)
    
# def single_write(txt, called_by='', meth='', direct=False, **args):
#     """similar to write but accept just one text arg and some more args"""
#     global DBG
#     global DBGLogger
#     if 'filter' not in args:
#         filter = None
    
#     if 'sfilter' not in args:
#         sfilter = None
    
#     if DBG == 0:
#         return
#     if direct and DBGLogger:
#         DBGLogger.write(txt=txt, line=caller(mode='lineno'), meth=meth,
#                         mode='write', caller=called_by)
#     else:
#         print "%s (line %s): %s" % (caller(), caller(mode='lineno'), txt)


    
def caller(mode=None, level=2):
    """
    mode can be:
    lineno:  just return line number for the calling frame
    loc:     return the local variables as dict
    None:    return (class_name, caller_func)
    Class :   return class
    instance : return class if applicable
    """
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

        if mode == 'Class':
            return a

        if mode == 'instance':
            return frame.f_locals['self']

    except:
        pass
    return "%s%s" % (class_name, caller)
    
def show_caller(filter=None, sfilter=None, loc=True):
    if DBG != 0:
        if loc:
            Locals = dshow(caller(mode='loc', level=3), ret=True,
                           filter=filter, sfilter=sfilter,mute=True)
        else:
            Locals = ''
            
        print "%s called from: %s (line %s) \n%s" % (
            caller(),
            caller(level=3), caller(level=3, mode='lineno'), Locals )
            
    
def dshow(diz, filter=None, sfilter=None, mute=False, ret=False, name=None):
    """print a dictionary in a friendly way
    filter:  only print keys that match 'filter'
    sfilter: only print keys that _don't_ match 'filter'
    """

    global DBG
    if DBG == 0:
        return
    txt = []
    if not mute:
        txt += [caller()]
    filtered = {}
    for k,v in diz.iteritems():
        if filter:
            if not re.search(filter, k):
                continue
        if sfilter:
            if re.search(sfilter, k):
                continue
        txt += ["    %s: %s" % (k, v)]
        filtered[k] = v
    if ret:
        return "\n".join(txt)
    else:
        try:
            iter = DBGLogger.write(meth=caller(), txt=name, mode='dict')
            for k,v in filtered.iteritems():
                DBGLogger.write(meth=k, txt=v, mode='value', parent=iter)
        except:
            print "\n".join(txt)

    
def ddir(obj, filter=None, sfilter=None, mute=False, ret=False):
    """print dir of an object in a readable fasion
    filter:  only print keys that match 'filter'
    sfilter: only print keys that _don't_ match 'filter'
    """

    global DBG
    if DBG == 0:
        return
    txt = []
    if not mute:
        txt += [caller()]
    for k in dir(obj):
        if filter:
            if not re.search(filter, k):
                continue
        if sfilter:
            if re.search(sfilter, k):
                continue
        v = getattr(obj, k)
        txt += ["    %s: %s" % (k, v)]
    if ret:
        return "\n".join(txt)
    else:
        print "\n".join(txt)

    
def warning(text):
    print text
    
def sql_debug(sql, params):
    msg = re.sub(':(?P<a>\S+)', '\'%(\g<a>)s\'', sql)
    #sd.debug("%s %s" % (DBG, params))
    print msg % params
    #write(msg % params)


indent = 0

### Trace
class TraceIt(object):
     """A data descriptor that sets and returns values
        normally and prints a message logging their access.
        Usi it in code like this::

           rowCommit = dbg.TraceIt(True, name='rowCommit', mode='rw')

     and use it as a normal variable.  You'll get lines in your output stating
     who changed the value of that variable, in the form::

     __str__/function_name:  old_value => new_value
     __get__/function_name:  value

     """

     def __init__(self, initval=None, name='var', mode='rw'):
         self.read = False
         if re.search('r', mode):
             self.read = True
             
         self.write = False
         if re.search('w', mode):
             self.write = True
             
         self.val = initval
         self.name = name

     def __get__(self, obj, objtype):

         if self.read:
             Caller = re.sub('.*\.([^\.]+$)', r'\1', caller(level=2))
             write("%s read %s" % (self.name, self.val),
                 called_by=Caller, meth='%s - r/%s' % (self.name, Caller))

         return self.val

     def __set__(self, obj, val):
         if self.write:
             Caller= re.sub('.*\.([^\.]+$)', r'\1', caller(level=2))
             write("%s: %s -> %s" % (self.name, self.val, val),
                 called_by=Caller, meth='%s - w/%s' % (self.name,Caller))
         self.val = val



### from a recepe in ASP:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/198078
def trace_class(ok=None, ko=None):
    """set pattern for classes that should be traced by LogTheMethods
    Rememeber that this command need to be issued before importing the package that
    should be traced
    """

    global CLASS_INCLUDE
    global CLASS_EXCLUDE
    if ok:
        CLASS_INCLUDE = ok

    if ko:
        CLASS_EXCLUDE = ko
        
def trace_function(exclude=None, include='.*'):
    """set pattern for functions/methods that should not be traced"""

    global FUNCTION_EXCLUDE
    global FUNCTION_INCLUDE

    if exclude:
        FUNCTION_EXCLUDE = re.compile(exclude)

    if not include == '.*':
        FUNCTION_INCLUDE = re.compile(exclude)
    
def logmethod(methodname):
    def _method(self,*argl,**argd):
        global indent
        global DBGLogger
        global DBG
        
        #print "DBG", methodname,  argl, argd
        #parse the arguments and create a string representation
        #import pdb; pdb.set_trace()
        args = []
        for item in argl:
            args.append('%s' % str(item))
        for key,item in argd.items():
            args.append('%s=%s' % (key,str(item)))
        argstr = ','.join(args)   
        
        caller1 = caller(level=1).replace('._method','')
        caller2 = caller(level=2)
        caller_class = caller1
        caller_meth = caller2
        
        try:
            class_str = self.nick
        except:
            class_str = caller_class
        if DBG:
            iter = DBGLogger.add(Class=class_str, meth=methodname, indent=indent,
                                 caller=caller_meth, line=caller(mode='lineno'),
                                 args=args, class_obj=caller(mode='Class'))
        
        indent += 1
        # do the actual method call
        try:
            f = getattr(self,'_H_%s' % methodname)

            returnval = f(*argl,**argd)
            
            indent -= 1
        except Exception, e:
            DBGLogger.add(Class=class_str, meth=str(e.__class__), indent=indent,
                                 caller=methodname, line=caller(mode='lineno'),
                                 args=e, class_obj=caller(mode='Class'))
            indent -= 1
            raise

        if DBG:
            ## iter is not defined if the method si not traced
            if iter:
                DBGLogger.ret(iter, str(returnval))

        return returnval
    
    return _method


class LogTheMethods(type):
    def __new__(cls, classname, bases, classdict):

        if re.search(CLASS_INCLUDE, classname):
            if not re.search(CLASS_EXCLUDE, classname):
                pass
        else:
            return type.__new__(cls,classname,bases,classdict)

        meths = {}

        meths.update(dict(classdict.items()))

        for base in bases:
            for attr in dir(base):
                # don't override the methods...
                if attr not in meths:
                    meths[attr] = getattr(base, attr)

        for attr, item in meths.items():
            if not DBG:
                continue
            if attr.startswith('_H_') or attr.startswith('__'):
                continue

            if callable(item) and FUNCTION_INCLUDE.match(attr) and  not \
                   FUNCTION_EXCLUDE.match(attr):
                if '_H_%s'%attr not in meths: # prevent infinite loop
                    classdict['_H_%s'%attr] = item    # rebind the method
                    classdict[attr] = logmethod(attr) # replace  by wrapper

        ret = type.__new__(cls, classname, bases, classdict)

        return ret

class ShowLogs(object):
    def __init__(self, model=None, show=False):
        global DBGLogger
        global logmodel
        if model is None:
            self.get_layout(show)
        DBGLogger = self

    def get_layout(self, show):
        import layout
        import layout.misc
        global iter
        self.last_indent = 0
        iter = {}
        self.indent = {}
        ## method, args, caller, line
        cols = ['meth','class', 'args', 'caller', 'line',
                'ret code', 'class', 'time', 'all_args']
        self.easytv = layout.misc.EasyTreeView(
            cols, sort=False, show=show, but='tb=gtk-close tb=gtk-open')
        self.time = time.time()
        self.last_time = time.time()
        self.model = self.easytv.model
        cell = self.easytv.tvc['meth'].get_cell_renderers()[0]
        self.easytv.tvc['meth'].set_attributes(cell, markup=0)
        self.easytv.l.connect(
            ('tb=gtk-open', 'clicked', lambda w, : self.easytv.tv.expand_all()),
            ('tb=gtk-close', 'clicked', lambda w, : self.easytv.tv.collapse_all()),
            ('tb=gtk-clear', 'clicked', self.model_clear),
            )

        logmodel = self.model
        self.iter = {}
        self.easytv.w['Window'].set_geometry_hints(
            self.easytv.w['Window'], min_width=500, min_height=500)
        self.model.connect('row-inserted', self.get_there)
        self.conf()
        self.easytv.tv.connect('button-press-event', self.button_press_cb)
        try:
            self.add_tooltips()
        except:
            pass
        
    def button_press_cb(self, wdg, ev):
        if ev.button != 3:
            return False
        iter = self.model.get_iter(
            wdg.get_path_at_pos(int(ev.x), int(ev.y))[0])
        obj = self.model.get_value(iter,6)
        meth = self.model.get_value(iter,0)
        meth = re.sub('<[^>]*>', '', meth)
        Hmeth = "_H_%s" % meth
        if Hmeth in dir(obj):
            self.info_method(obj, Hmeth)
            return
        else:
            print "No %s in %s" % (Hmeth, obj)

        if meth in dir(obj):
            self.info_method(obj, meth)

        return

    def info_method(self, obj, meth):
        """show info on method 'obj' using text widget"""

        try:
            attr = getattr(obj, meth)
            inspect.getsourcelinesattr(attr)[1]
        except:
            for i in obj.__bases__:
                try:
                    attr = self.info_method(i, meth)
                    inspect.getsourcelinesattr(attr)[1]
                    return
                except:
                    print "NOT FOUND in __bases__", i
                    return
                    pass
        obj = attr

        l = layout.Layout('TXS=a:700.400',opts="V")
        w=l.show()
        buff = w['TX=a'].get_buffer()
        
        self.configure_buffer(buff)
        txt = []
        try:
            txt.extend("# defined at line %s of file:\n# %s\n# module: %s\n\n" %(
                inspect.getsourcelines(obj)[1],
                inspect.getfile(obj),
                inspect.getmodule(obj),
                ))
        except TypeError:
            txt.extend("Built-in function/method or class")

        txt.extend(inspect.getsource(obj))
        #buff.set_text(txt)
        self.insert_source("".join(txt), buff)

    def add_tooltips(self):
        tips = DebugTreeView(self.model)
        tips.add_view(self.easytv.tv)

    def insert_source(self, data, buf):
        buf.delete(*buf.get_bounds())
        iter = buf.get_iter_at_offset(0)
        #print buf.get_tag_table()
        last_erow, last_ecol = 0, 0
        was_newline = False # multiline statement detection
        old_str = None
        for x in tokenize.generate_tokens(layout.misc.InputStream(data).readline):
            # x has 5-tuples
            tok_type, tok_str = x[0], x[1]
            srow, scol = x[2]
            erow, ecol = x[3]
            #dbg.write("type %s -- src: .%s." % (tok_type, tok_str))

            # The tokenizer 'eats' the whitespaces, so we have to insert this again
            # if needed.
            if srow == last_erow:
                # Same line, spaces between statements
                if scol != last_ecol:
                    buf.insert_with_tags_by_name(iter, ' '*(scol-last_ecol), 'source')
            else:
                # New line.
                # First: Detect multiline statements. There is no special in the tokenizer stream.
                if was_newline is False and last_erow != 0:
                    buf.insert_with_tags_by_name(iter, ' \\\n', 'source')
                # new line check if it starts with col 0
                if scol != 0:
                    buf.insert_with_tags_by_name(iter, ' '*scol, 'source')
            last_erow = erow
            last_ecol = ecol

            if tok_type == tokenize.COMMENT:
                was_newline = True # newline is in tok_str included.
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'comment')
                old_str = tok_str
                continue
            
            if tok_str.startswith('"""'):
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'docstring')
                old_str = tok_str
                continue
                
            if old_str == 'def':
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'function')
                old_str = tok_str
                continue
                
            if old_str == 'class':
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'class')
                old_str = tok_str
                continue
                
            elif tok_type == tokenize.NAME or tok_str == 'self':
                if tok_str in keyword.kwlist + ['self']:
                    buf.insert_with_tags_by_name(iter, tok_str, 'source', 'keyword')
                    old_str = tok_str
                    continue
            elif tok_type == tokenize.STRING:
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'string')
                old_str = tok_str
                continue

            # No special format for use. Check for newline.
            was_newline = tok_type in (tokenize.NEWLINE, tokenize.NL)
            buf.insert_with_tags_by_name(iter, tok_str, 'source')
            old_str = tok_str

    def configure_buffer(self, buf):
        #print "Configuro %s" % buf
        tag = buf.create_tag('title')
        tag.set_property('font', 'Sans 18')

        tag = buf.create_tag('source')
        tag.set_property('font', 'monospace')
        tag.set_property('pixels_above_lines', 0)
        tag.set_property('pixels_below_lines', 0)
        tag = buf.create_tag('keyword', foreground='mediumorchid',
                                weight=pango.WEIGHT_BOLD)
        tag = buf.create_tag('string', foreground='royalblue4')
        tag = buf.create_tag('function', foreground='blue')
        tag = buf.create_tag('docstring', foreground='indianred')
        tag = buf.create_tag('class', foreground='#007F00')
        tag = buf.create_tag('comment', foreground='red',
                                       style=pango.STYLE_ITALIC)
        

        
        
    
    def model_clear(self, butt):
        self.model.clear()
        self.iter = {}

    def get_there(self, model, path, iter):
        self.easytv.tv.scroll_to_cell(path)
        self.easytv.tv.expand_to_path(path)
        
    def show(self):
        self.easytv.show()

    def conf(self, but='^$', only='.*'):
        self.but = re.compile(but)
        self.only = re.compile(only)
        
    def log(self, obj, but='^$', only='.*'):
        #but = re.compile(but)
        #only = re.compile(only)
        for attr in dir(obj):
            if attr.startswith('__') and attr != '__init__':
                continue
            if but.search(attr):
                continue
#             if not only.search(attr):
#                 continue
            item = getattr(obj, attr)
            if callable(item):
                anInstance = item.im_self
                anInstance.__dict__['_H_%s' % attr] = item
                anInstance.__dict__[attr] = new.instancemethod(
                    logmethod(attr), anInstance, anInstance.__class__)

    def add(self, txt='', Class='', line=None,
              caller='', meth=None, indent=0, args=[], ret=None,
              class_obj=None):
        """adds to the TreeModel. If a method is called from another, its line
        will be a sun of the previous and the color will be changed with
        markup
        """
        col = {0: 'navyblue', 1:'slateblue', 2:'red', 3: 'seagreen',
               4: 'gray50', 5: 'gray60', 6: 'gray65', 7:'gray70'}


        if self.but.search(meth):
            return
#         if not self.only.search(but):
#             print 'KO only', meth
#             return

        meth_str = meth
        meth_str = "<span foreground='%s'>%s</span>" % (
            col.get(indent, 'palevioletred'), self.quote(meth))

        self.last_indent = indent

        if indent == 0:  
            self.iter[indent] = self.model.append(None)
        else:
            self.iter[indent] = self.model.append(self.iter.get(indent-1, None))

        try:
            txt = args[0]
        except IndexError:
            txt = ''
        now = time.time()
        self.model.set(  self.iter[indent],
                         1, Class,
                         0, meth_str,
#                         2, txt,
                         2, ", ".join(args),
                         3, caller,
                         4, line,
                         6, class_obj,
                         7, "%.3f - %.4f" % (now - self.time, now - self.last_time),
                         8, args,
                         )
        self.last_time = now
        ## args to the functions are written one per line, the first is already
        ## written, now the other come...
#         for arg in args[1:]:
#             self.model.set(self.model.append(self.iter[indent]),
#                       2, arg[0:100]
#                       )
        self.indent[meth] = indent
        #print "self.indent[%s] = %s" % (meth, indent)
        return self.iter[indent]


    def write(self, niter=None, txt='', line=None, mode=None, parent=None,
              caller='', meth=None, indent=None, args=[], ret=None, Class=''):

        # I want to try to indent all logs (write) as the caller
        try:
            indent = self.indent[caller]
        except:
            indent = self.last_indent

        if parent:
            iter = self.model.append(parent)
        else:
            #self.iter[indent] = self.model.append(None)
            try:
                iter = self.model.append(self.iter[indent-1])
            except:
                try:
                    iter = self.model.append(self.iter[indent])
                except KeyError:
                    iter = self.model.append(None)
        color={
            'dict' : 'green',
            'value' : 'seagreen',
            'write' : 'blue',
            }
        meth = re.sub('(.*)\.(.*)',r'\2', str(meth))
        meth_str = "<span foreground='%s'>%s</span>" % (
            color[mode], self.quote(meth))

        now = time.time()
        self.model.set(  iter,
                         0, "(%s)" % meth_str,
                         1, Class,
                         2, txt,
                         3, caller,
                         4, line,
                         7, "%.3f - %.4f" % (now - self.time, now - self.last_time)
            )
        self.last_time = now

        return iter

    def quote(self, text):
        """quote string from undesired chars in pango markup"""
        #text = re.sub('([<\'>])', r'\\\1', text)
        text = re.sub('([<\'>])', '', text)
        return text
    
    def ret(self, iter, txt):
        self.model.set(iter, 5, txt[0:100])
        return iter

#DBGLogger = LogTheMethods()

try:
    from TreeViewTooltips import TreeViewTooltips
    class DebugTreeView(TreeViewTooltips):
        def __init__(self, model):
            self.model = model
            TreeViewTooltips.__init__(self)


        def quote(self, text):
            """quote string from undesired chars in pango markup"""
            text = re.sub('([<\'>])', '', str(text))
            return text

        def get_tooltip(self, view, column, path):
            meth, args, ret, caller, line = self.model.get(
                self.model.get_iter(path), 0, 2, 5, 3, 4)
            ret  = re.sub('[<>]','', str(ret))
            args = re.sub('[<>]','', str(args))
            
            try:
                caller = ".".join(caller.split('.')[-2:])
            except:
                pass
            caller = re.sub('[<>]','', str(caller))

            txt = """<i>%s</i>(<tt>%s</tt>)\n<b>%s</b>\n<i>%s:%s</i>""" % (
                meth, args, ret, caller, line
        )
            return txt
except:
    pass
