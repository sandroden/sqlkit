#!/bin/env python
# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# 

import sys
sys.path.append ('../../../')
from sqlalchemy import *
from layout import *


#sys.path.append('../gdl')

if sys.hexversion < 0x20401f0:
    print "your python version: ", hex(sys.hexversion)
    print "needed python version >= ", hex(0x20401f0)
    sys.exit(-1)
    
import gtk, gobject
#import layout
from SqlChecker import *
from sqlalchemy import *


class SqlTreeView(object):

    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    rowCommit = True

    
    def __init__(self, treeview, MappedClass, rowCommit=True, checkClass=None):

        if checkClass is not None:
            checkObj = checkClass(self)
        self.mc = MappedClass
        self.rowCommit = rowCommit

        #setup a ListStore
        self.mapToListStore()
        #create the treeview
        self.treeview = treeview
        self.treeview.set_model(self.liststore)
        
        self.treeview.set_rules_hint(True)
        #set selection mode
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        self.__init_accelerators()
        #callback for selection changes
        treeselection.connect('changed', self.selection_changed_cb)
        self.treeview.connect('cursor-changed', self.cursor_changed_cb)
        self.treeview.connect('select-cursor-row', self.select_cursor_row_cb)
        #register callback to toplevel window
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)
        #create and append columns
        for i,v in enumerate(self.mc.mapper.c.keys()):
            cell = gtk.CellRendererText()
            cell.set_property('editable', True)
            cell.set_property('editable-set', True)
            cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
            tvcolumn = gtk.TreeViewColumn(v.replace('_','__'))
            tvcolumn.pack_start(cell, True)
            tvcolumn.add_attribute(cell, 'text', i + 1)
            cell.connect('edited', self.edited_signal, (self.liststore, i))
            cell.connect('editing-started', self.text_editing_started, i)
            tvcolumn.set_cell_data_func(cell, self.set_special_attributes, i)
            self.treeview.append_column(tvcolumn)

    def __init_accelerators(self):
        """Initializes keyboard accelerators"""

        self.treeview.connect('key-press-event', self.keypress_event)

    def tab_pressed(self, treeview):
        print "tab_pressed", treeview
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum + 1 < len(columns):
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum+1], True)
        else:
            tmodel = self.treeview.get_model()
            titer = tmodel.iter_next(tmodel.get_iter(path))
            print "TreeIter", titer
            if titer is None:
                titer = tmodel.get_iter_first()
            path = tmodel.get_path(titer)
            gobject.idle_add(self.treeview.set_cursor, path, columns[0], True)
        return

    def ltab_pressed(self, treeview):
        print "ltab_pressed", treeview
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum - 1 >= 0:
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum-1], True)
        else:
            path = (path[0] - 1,)
            if path[0] < 0:
                path = (len(treeview.get_model()) - 1,)
            gobject.idle_add(self.treeview.set_cursor, path, columns[-1], True)
        return

    def keypress_event(self, treeview, event):
        print "key", gtk.accelerator_name(event.keyval, event.state)
        accelname = gtk.accelerator_name(event.keyval, event.state)
        if accelname == 'Tab':
            self.tab_pressed(treeview)
            return True
        elif accelname == '<Shift>ISO_Left_Tab':
            self.ltab_pressed(treeview)
            return True
        return False

    def select_cursor_row_cb(self, treeview, start_editing, user_data = None):
        #print "select_cursor_row_cb"
        return False
    
    def cursor_changed_cb(self, treeview, user_data = None):
        #print "cursor_changed_cb"
        return False
        
    def selection_changed_cb(self, treeselection):
        if self.rowCommit:
            print "row changed: commit"
            objectstore.commit()
        return False

    def text_editing_started(self, cell, editable, path, col):
        completion = gtk.EntryCompletion()
        editable.set_completion(completion)
        completion.set_model(self.liststore)
        completion.set_text_column(col + 1)
        return True
    
    def edited_signal(self, cell, path, new_text, user_data):
        print "edited_signal"

        liststore, colnum = user_data
	
	try:
	    data = self.coltypes[colnum + 1](new_text)
	except TypeError:
	    try:
		from mx.DateTime import DateTimeType, DateTimeFrom
	    except ImportError:
		#use a string
		data = str(new_text)
		raise ImportError
	    else:
		if self.coltypes[colnum + 1] is DateTimeType:
		    data = DateTimeFrom(str(new_text))
		else:
		    print self.coltypes[colnum + 1]
		    data = str(new_text)
	
        liststore[path][colnum + 1] = data
        r = liststore[path][0]
        setattr(r, r.c.keys()[colnum], data)
        return True
    
        
    def set_special_attributes(self, column, cell_renderer, tree_model, iter, i):
        pass

    def insertRow(self, button):
        #print "inserting row in liststore"
        rowCommit = self.rowCommit
        self.rowCommit = False
        col = self.treeview.get_column(0)
        #print "setting cursor"
        self.liststore.prepend()
        self.liststore[0][0] = self.mc()
        self.treeview.scroll_to_cell("0", col)
        self.treeview.set_cursor(path = "0",
                                 focus_column = col,
                                 start_editing = True)
        #print "finished inserting"
        self.rowCommit = rowCommit

        return True

    def deleteRow(self, button):
        def do_del(tm, path, iter):
            #print "deleting row in liststore"
            print tm[path][0]
            tm[path][0].delete()
            del tm[path]

        sel = self.treeview.get_selection()
        sel.selected_foreach(do_del)
        #print "finished deleting"

        return True

    def mapToListStore(self):
        # suppose there is at least one record(?)
        colnames = self.mc.mapper.c.keys()
        self.coltypes = [object]
        self.coltypes.extend([type(getattr(self.mc.mapper.select()[0],x)) for x in colnames])
	coltypes = [object]
	print self.coltypes
	# try to convert types to gobject types
	for tp in self.coltypes[1: ]:
	    try:
		coltypes.append(gobject.type_from_name(gobject.type_name(tp)))
	    except TypeError:
		coltypes.append(str)

	print coltypes
        self.liststore = gtk.ListStore(*coltypes)
        #fill up
        for r in self.mc.mapper.select():
            values = [getattr(r, x) for x in colnames]
            #prepend r itself
            values.insert(0, r)
            self.liststore.append(values)
    
    def delete_event(self, treeview, event, data=None):
        print "delete_event: committing work"
        objectstore.commit()
        return False

        
    
class SqlLayoutTreeView(SqlTreeView):

    def __init__(self, MappedClass, checkClass=None):
                ### The layout
        lay = """
          {B m=file m=modifica m=opzioni m=aiuto}
          {O tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-quit}
          TVS=tree
        """
        self.l = Layout(lay,opts='s', title="ListStorageView")
        self.w = self.l.show(x=self.delete_event)
        self.window = self.w['Window']
        self.l.menu('m=file',
                    ('gtk-open', self.insertRow,),
                    ('-',None,),
                    ('gtk-quit', self.exit_now)
                    )

        self.w['tb=gtk-delete'].connect('clicked', self.deleteRow)
        self.w['tb=gtk-new'].connect('clicked', self.insertRow)
        self.w['tb=gtk-quit'].connect('clicked', self.exit_now)

        #self.l.connect(
        #    ('tb=gtk-delete', 'clicked', self.deleteRow),
        #    ('tb=gtk-new',    'clicked', self.insertRow),
        #    ('tb=gtk-quit',   'clicked', self.exit_now )
        #    )
        

        # accel group  #### FIXME: dove viene usato?
        #accel_group = gtk.AccelGroup()
        #self.window.add_accel_group(accel_group)
        treeview = self.w['TV=tree']

        SqlTreeView.__init__(self, treeview, MappedClass,
                             checkClass=checkClass)
        

    def delete_event(self, w, e):
        SqlTreeView.delete_event(self, w, e)
        gtk.main_quit()
        return False

    def exit_now(self, widget):
        self.delete_event(widget, None)
        return True
