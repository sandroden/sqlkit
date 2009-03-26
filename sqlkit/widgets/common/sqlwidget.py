# Copyright (C) 2005-2006-2007-2008, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import re
import datetime
import os
import inspect 
from sqlkit import layout
from sqlkit.layout import map_labels, get_label
import sqlalchemy.types as sqltypes
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import Table

from layoutgenerator import LayoutGenerator
import gtk, pango
import decimal
from sqlalchemy import exceptions
from sqlalchemy.orm import scoped_session, sessionmaker, class_mapper
#from sqlalchemy import *
from sqlkit import debug as  dbg

import gobject
import sqlfilter
#from sqlkit.widgets.common import sqlfilter2 as sqlfilter
from sqlkit.db import minspect, defaults
from sqlkit.widgets.common import completion
from sqlalchemy.orm import attributes
from sqlkit.misc.utils import Container
import sqlkit
from sqlkit import _, exc
from babel import numbers

NUMBERS = (int, float, decimal.Decimal)

class SqlWidget(gobject.GObject):
    __gsignals__ = {
        'record-selected' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                           (),
                           ),
        'records-displayed' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                           (),
                           ),
        'after-flush' :    (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                            # object, new, dirty, deleted
                           (gobject.TYPE_PYOBJECT , gobject.TYPE_PYOBJECT ),
                            ),
        'delete-event' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                           (),
                           ),

                            }
    gui_fields = None
    values = None    # real value for foreign key
                     # (when lookup is displeyed instead)
#    __metaclass__ = dbg.LogTheMethods
    records = None
    last_new_obj = None

    def __init__(self, mapper=None,
                 ## geometry
                 layout = None,
                 naked=False,
                 geom=(-1,-1),
                 rows=10,
                 addto=None,
                 title=None,
                 show=True,
                 icons='',
                 col_width = None,
                 # SQL
                 table=None,
                 tables=None,
                 class_=None,
                 join=None,
                 ro=False,
                 noup=[],
                 sql=None,
                 constraint={},
                 dbproxy = None,
                 order_by=None,
                 limit=200,
                 field_list=None,
                 session=None,
                 metadata = None,
                 ignore_fields = None,
                 hide_fields = None,
                 ## more
                 single=False,
                 nick=None,
                 about_dialog = None,
                 dev=False,
                 xml=False,
                 relationship_mode = 'SINGLE',
                 relationship_path = None,
                 relationship_leader = None,
                 format=None,
                 label_map = None,
                 ):

        """
        create an interface and allow to save/store data from a database

        layout:    a layout describing the desired layout (see layout package)
        naked:  in case the mask should *not* be added interactive buttons
                needed if the layout already contains all the required buttons
        ro:     Boolean. When in read-only no save/delete is alllowed
        noup:   list of field-name that cannot be updated, may be a comma
                separated str
        show:   True|False
        single: this is a single application. connect a gtk.quit()
        nick is just for debug purpouse
        addto:  passed to layout
        dev:    if dev=False (default) fields ending with '_id' and not fk
                are not shown
        hide:   fields not to be shown (space or comma separated or list)
        class_:  an instrumented class (one connected o a mapper). This along with
                session may be the only parameters
        table[s]: a table name. The plural is left for a possibe extensions to automatic join
        mapper: a sqlalchemy mapper. a Class is built runtime, metadata is read from local_table
        session: the session where to put all data.

        relationship_mode: SINGLE, FIXED, m2m, m2o, o2m
                FIXED: any filter/reload is inibited
        relationship_path: the path needed to join two tables. See sqlalchemy on 'quering
                  with joins'. Used by filter_panel to setup join condition when filtering
                  when relationship_mode is not SINGLE. May be a list or a string:
                  'genres', 'director nationality', ['director','nationality']
        relationship_leader: the main sqlmask (sqltable) that "owns" the filter_panel
        format: a format dict as for set_format, settings formatting info for numbers and dates
        """

        gobject.GObject.__init__(self)
        self.related = Container()
        self.gui_fields = Container(self.gui_fields)
        self.field_widgets = Container()
        self.completions = Container()
        self.label_map = map_labels(buf=label_map, private=True)
        self.icons = icons
        self.col_width = col_width
#        self.filter = filter
        self.xml = xml
        self.dev = dev
        # used in self.reload() to prevent expose loop 
        self.reloading = dbg.TraceIt(False, name='reloading')
        self.geom = geom
        self.addto = addto
#        self.actions = self.get_actions(actions)
        self.constraint=constraint
        self.dbproxy = dbproxy
#        self.engine = self.get_engine(engine, mapper)
        self.session = self.get_session(session)
        self.order_by = order_by
        self.mapper = self.get_mapper(mapper, table or tables, class_)
        self.metadata = self.get_metadata(metadata, self.mapper)
        ## we can use singular or plural as an option, plural in the code
        if table and not tables:
            tables = table
        self.tables = self.get_table(tables)
        self.nick= self.get_nick(nick)
        self.ro = ro
        self.noup = noup
        self.rows = rows
        self.hidden_fields = hide_fields or []
        self.mapper_info = self.get_fields()
        self.field_list = self.parse_fields(field_list, layout)
        self.ignored_fields = self._set_ignored_fields(ignore_fields)
        if hide_fields:
            self.hide_fields(force=True)
        self._title = self._create_title(title)
#        self.tables = {}
        self.values = {}
        ## create the interface and add obvious constraints
        self.naked = naked
        self.lay   = layout
        self.sql   = sql
        self.single = single
        self.limit=limit
        self.relationship_mode = relationship_mode
        self.relationship_path = self._get_relationship_path(relationship_path)
        self.relationship_leader = relationship_leader
        self.records = []
        self.about_dialog = about_dialog or self.create_about_dialog()
        self.filter_panel = self._get_filter_panel()
        self.show(show)
        self.set_format(format)
        self.query = self.session.query(self.mapper)
        self.defaults = defaults.Defaults(self.tables, metadata=self.metadata, local=True)
            
    def get_session(self, session):
        if session:
            return session
        else:
            return self.dbproxy.get_session()
    
    def get_mapper(self, mapper, tables, class_=None):

        if mapper:
            return mapper
        elif class_:
            mapper = class_mapper(class_)
        else:
            mapper = self.dbproxy.get_mapper(mapper, tables)
            
        #self.tables = [mapper.local_table.name]  ## FIXME: what when we have a join?
        return mapper

    def get_metadata(self, metadata, mapper):
        if metadata:
            return metadata
        if self.dbproxy:
            return self.dbproxy.metadata
        if mapper:
            ## FIXME: no good in general? what if you have more that
            ## one metadata in the same session?... boh
            return mapper.local_table.metadata
        
    def get_table(self, tables):
        if isinstance(tables, Table):
            return tables.name
        if tables:
            return tables.split()[0]  ## FIXME: works for 1 single table
        if self.mapper:
            try:
                return self.mapper.local_table.name
            except Exception, e:
                print e
                return None

    def parse_fields(self, field_list, layout):
        if not field_list:
            ### if no layout was defined and no field_list was passed
            ### we don't add PropertyLoader (ManyToMany relations):
            ### we would't know where to represent them.
            ###
            ### If a layout was defined, we add propertyLoader only for SqlMask
            ###
            if self.is_mask() and layout:
                get_the_keys = self.mapper_info.all_keys
            else:
                get_the_keys = self.mapper_info.keys
                
            if self.dev:
                new_field_list = get_the_keys()
            else:
                ## I want all fields not ending with _id
                ## *AND* all fields that REFERENCE other keys
                ## i.e.: if you have city_id that references a city I want
                ## to see it, but I don't want to see a sequence normally.
                new_field_list = [f for f in get_the_keys()
                          if not f == 'id' or self.mapper_info.fields[f]['fkey'] ]

            
        else:
            if isinstance(field_list, str):
                new_field_list = [f for f in re.split('[ ,]+',field_list) if f]
            else:
                new_field_list = field_list
        return new_field_list
    
    def _get_relationship_path(self, path):
        """
        relationship_path is the path needed to get from the main sqlwiget to here:
        if movie has an attributes 'genres' that is set as a relation to it, the 'path'
        of the SqlTable of the genres will be: ['genres'].

        It's used in filter widgets
        """

        self.m2m_editable = False
        if not path:
            return []
        
        if isinstance(path, (tuple, list)):
            return path
        else:
            return re.split("[ ,]+", path)
        
    def get_pk(self):
        """
        return the pkeys of the primarytable
        """
        return self.mapper_info.pkeys[self.mapper_info.get_primary_table()]

###### Filters/constraints
    def add_constraint(self, OR=False, *args, **kwargs):
        """
        Add constraints. A constraint may be one or more ColumnElement, ColumnList
        or django-like syntax. Eg.::

           name_like='uno%'
           genres__name__regexp='sto'
           director_id__birth_date__gte='1/1/1970'

        if multiple conditions are passed, they will be ANDed unless 'or_=True'
        """
        from sqlkit.db.django_syntax import django2query
        self.query = django2query(self.mapper, self.query, OR=OR, *args, **kwargs)
        
    def add_filter_cb(self, event=None, visible=True):
        """
        Pop a Filter Panel, called from menu item
        """
        self.filter_panel.w['Window'].present()

    def add_filter(self, **kw):
        self.filter_panel.add_filter(**kw)
        
###### Layout

    def _get_layout(self, lay, naked):
        """
        lay may be a definition string or another SqlMask in case the layout has
        just been build by another SqlMask object and we just need to
        add controls and so on
        """
        self.get_table_labels()
        if self.is_mask(lay):
            self.widgets = lay.widgets
            self.filter_panel = lay.filter_panel
            ## NOTE: here I say that I can reach w/ get_value also the
            ##       values of the secondary mask. Of course you need to be
            ##       carefull not to mix up filed-names
            self.mfields = lay.mfields
            self._analize_widgets_in_layout()
            self._add_click_for_filter()
            self._add_color_to_labels()
            self.values = lay.values
            return (lay.lay_obj, lay.widgets)
        
        self.laygen = LayoutGenerator(self, naked=naked, lay=lay)
        lay = self.laygen.layout
        self.lay_obj = layout.Layout(lay, addto=self.addto,
                                     title=self._title, opts='T-', label_map=self.label_map)
        #if self.xml:
        #    self.lay_obj.xml('/tmp/m_%s.glade' % self.nick)

        if 'Window' in self.lay_obj.elements:
            self.lay_obj.prop('Window', 'visible', False)

        self.widgets = self.lay_obj.show()

        if 'A.external' in self.widgets:
            external_align = self.widgets['A.external']
            table = external_align.get_parent()
            table.child_set_property(external_align, 'y-options', gtk.EXPAND | gtk.FILL)

        if 'S=tree' in self.widgets:
            internal_align = self.widgets['S=tree']
            table = internal_align.get_parent()
            table.child_set_property(internal_align, 'y-options', gtk.EXPAND | gtk.FILL)

        if self.is_toplevel():
            self.lay_obj.connect(('Window', 'delete_event', self.delete_event_cb))
            if self.geom:
                self.resize(*self.geom)

        self.setup_field_validation()
        self.prepare_actions()
        self.prepare_uimanager()

        return (self.lay_obj, self.widgets)
    
    def show(self, show):
        """
        create the widget and go on displaying the layout
        """
        self.lay_obj, self.widgets  = self._get_layout(self.lay, self.naked,)
            
        ## only render when dimentions are complete
        lcontainer_name = self.lay_obj.container().el_def
        el_def = re.sub(':.*','', lcontainer_name)

        if show:
            self.widgets[el_def].show()

        if self.relationship_mode == 'FIXED':
            self.actiongroup_edit.set_sensitive(True)
            self.actiongroup_browse.set_sensitive(False)
            
    def _set_ignored_fields(self, ignored_list):
        """
        Ignored fields will not even be in self.field_list
        """

        if isinstance(ignored_list, str):
            ignored_list = re.split('[ ,]+', ignored_list)

        if not ignored_list:
            return None
        
        for field_name in ignored_list:
            if field_name in self.field_list:
                self.field_list.remove(field_name)

        return ignored_list
        
    def hide_fields(self, *args):
        """
        """
        self.dialog(type="ok", text=_("Hiding field is only supported for Tables"))
        
    def get_nick(self, nick):
        if not nick:
            if self.tables:
                nick = self.tables
            else:
                nick = self.mapper.tables[0].name
        return nick
            
    def get_fields(self):
        """Fields is a dictionary with info on the fields derived from the
        db via the mapper (inspecting it)
        """
        info = minspect.InspectMapper(self.mapper, noup=self.noup, ro=self.ro)
        ## fix column_width that may have been passed
        if self.col_width:
            for field_name, value in self.col_width.items():
                if field_name in info:
                    info.fields[field_name]['length'] = value
        return info
        
    def _get_filter_panel(self):
        if self.relationship_leader:
            return self.relationship_leader.filter_panel
        
        return sqlfilter.FilterPanel(self, visible=False)

    def _set_title(self, title):

        if self.is_toplevel():
            self.widgets['Window'].set_title(title)
        self._title = title
        
    def _get_title(self):
        
        if self.is_toplevel():
            return self.widgets['Window'].get_title(title)
        else:
            return getattr(self, '_title', None)
        
    title = property(_get_title, _set_title)
            
    def grab_focus(self, widget):
        """
        make sure the focus is grabbed so that all validation-related triggers
        update correctly. If the widget cannot get focus, try tb=gtk-save
        """

        sqlwidget = self.relationship_leader or self
        save_widget = sqlwidget.ui_manager.get_widget('/Main/File')
        save_widget.grab_focus()
        
    def sb(self, text, seconds=10):
        """
        write on the status bar, if present
        """

        if self.relationship_leader:
            self.relationship_leader.sb(text, seconds=seconds)
        else:
            try:
                self.lay_obj.sb(text, seconds=seconds)
            except Exception, e:
                #print e, vars(e)
                pass

    def _create_title(self, title=None):
        if not title:
            try:
                title=self.table
            except:
                title= self.mapper_info.get_primary_table()
        return title
    
    def get_table_labels(self):
        """
        get labels and tipd from the db is they exists
        """
        from sqlkit.db.utils import get_labels_and_tips_from_sqlkit
        for table in self.tables.split():
            self.label_map.update( get_labels_and_tips_from_sqlkit(table, metadata=self.metadata))
            
    def resize(self, width, height):
        """
        Resize the parent window
        """
        if width < 0 or height < 0:
            return
        gobject.idle_add(self.widgets['Window'].resize, width, height)
        
    def get_table_label(self):
        """
        get labels and tips from the db is they exists
        """
        from sqlkit.db.utils import get_labels_and_tips_from_sqlkit
        for table in self.tables.split():
            self.label_map.update( get_labels_and_tips_from_sqlkit(table, metadata=self.metadata))
            
    def gquit(self, *args):
        gtk.main_quit()
                       
###### Actions/UiManager
    def prepare_actions(self):
        """
        Prepare action needed by UIManager
        """
        self.actiongroup_general = gtk.ActionGroup('General')
        self.actiongroup_edit  = gtk.ActionGroup('Edit')
        self.actiongroup_browse  = gtk.ActionGroup('Browse')
        self.actiongroup_print   = gtk.ActionGroup('Print')    
        self.actiongroup_debug   = gtk.ActionGroup('Debug')    

        self.actiongroup_general.add_actions([
            ('File', None, 'File' ),
            ('Modify', None, '_Modify' ),
            ('Go', None, '_Go' ),
            ('Tools', None, '_Tools' ),
            ('Help', None, '_Help' ),

            ('Quit', gtk.STOCK_QUIT, None, '<Ctrl>q', None, self.delete_event_cb),
            ('About', gtk.STOCK_ABOUT, None, None, None, self.about_dialog_cb),
            ])

        self.actiongroup_edit.add_actions([
            ('Save', gtk.STOCK_SAVE, None, '<Ctrl>s', None, self.record_save_cb),
            ])

        self.actiongroup_browse.add_actions([
            ('Filters', gtk.STOCK_FIND, _('Filter panel'), None, None, self.add_filter_cb),
            ('Reload', gtk.STOCK_REFRESH, _("Reload"), '<Ctrl>r', None, self.reload_cb),
            ('Forward', gtk.STOCK_GO_FORWARD, None, '<Alt>f', None, self.record_forward_cb),
            ('Back',   gtk.STOCK_GO_BACK, None, '<Alt>b', None, self.record_back_cb),
            ])

        self.actiongroup_print.add_actions([
            ])

        self.actiongroup_debug.add_actions([
            ('Gtk-tree', gtk.STOCK_EXECUTE, _('Inspect widgets'), '<Ctrl><Alt>i', None, self.show_widget_info),
            ])

    def prepare_uimanager(self):
        """
        Prepare UIManager, actions, and accelerators
        """

        import uidescription

        self.ui_manager = gtk.UIManager()

        if self.is_toplevel():
            self.accel_group = self.ui_manager.get_accel_group()
            self.widgets['Window'].add_accel_group(self.accel_group)

        self.ui_manager.add_ui_from_string(uidescription.GENERAL_UI)
        self.ui_browse_id = self.ui_manager.add_ui_from_string(uidescription.BROWSE_UI)
        self.ui_debug_id = self.ui_manager.add_ui_from_string(uidescription.DEBUG_UI)

        self.ui_manager.insert_action_group(self.actiongroup_general, 0)
        self.ui_manager.insert_action_group(self.actiongroup_edit, 1)
        self.ui_manager.insert_action_group(self.actiongroup_browse, 2)
        self.ui_manager.insert_action_group(self.actiongroup_print, 3)
        self.ui_manager.insert_action_group(self.actiongroup_debug, 4)

        ## pack menu and toolbar if it's a toplevel
        if 'V.header' in self.widgets:
            header = self.widgets['V.header']
            menu    = self.ui_manager.get_widget('/Main')
            toolbar = self.ui_manager.get_widget('/TbMain')
            header.add(menu)
            header.add(toolbar)

###### Saving
    def record_delete(self, widget=None):
        """invokes the validator before DELETing a record"""
        pass
    
    def record_save_cb(self, widget, event=None):
        """Save the record and invokes the validator before UPDATE/INSERT a record
        """
        try:
            self.record_save()
        except (sqlkit.exc.CancelledAction, sqlkit.exc.ValidationError):
            pass
    
    def record_new_cb(self, widget, event=None):
        """Save the record and invokes the validator before UPDATE/INSERT a record
        """
        try:
            self.record_new()
        except (sqlkit.exc.ValidationError, sqlkit.exc.CancelledAction):
            return True
    
    def record_save_new(self, ev):
        """
        Save the record as a new record, ie letting pk not be set 
        """
        raise NotImplementedError

    def commit(self, message=_('Saved')):
        from sqlkit.db.proxy import SKSessionExtension
        
        if self.ro:
            return
        try:
            ## when session.autocomit = False, a transaction is automatically started
            obj = self.get_current_obj()

            ## this is needed for after-flush signal emission that is implemented inside
            ## SKSessionExtension
            for extension in self.session.extensions:
                if isinstance(extension, SKSessionExtension): 
                    extension.sk_sqlwidget = self
                    extension.sk_current = obj

            if self.session.autocommit:
                self.session.begin()
                
            self.session.commit()
                
            self.sb(message, seconds=3)

        except (exceptions.DBAPIError, exceptions.FlushError), e:
            if not self.commit_error_handler(e):
                self.session.rollback()

    def commit_error_handler(self, e):
        """
        communicate the problem to the user
        return True to prevent rollback
        """
        if isinstance(e, exceptions.IntegrityError):
            # TIP: message in the status bar when a commit error is handled
            msg = _("Error while writing to the database. Possible causes: you are saving \n" + \
                  "an already existent record or deleting a record that is referenced by other " \
                  "records. \nOriginal error was: \n%s") % e.message
            self.message(type='error', text=_(msg))
            self.sb(e.message)

        elif isinstance(e, exceptions.DBAPIError):
            # TIP: message in the status bar when a commit error is handled
            self.message(type='error',
                         text=_("%s - Dirty objects: %s - New objects: %s") % \
                         (str(e.orig),len(self.session.dirty),len(self.session.new)))
            self.sb(e.orig)

        elif isinstance(e, exceptions.FlushError):
            # TIP: message in the status bar when a commit error is handled
            msg = _("Error while writing to the database: \n" \
                    "are you 'saving as new' an already known record?\n" + \
                    "original error was: \n%s") % e.message
            self.message(type='error', text=_(msg))
            self.sb(e.message)

        return False  # i.e.: rollback

    def get_value(self, field_name):
        """
        to be overwritten by Mask & Table
        """
        return NotImplementedError
    
    def set_value(self, field_name, value):
        """
        to be overwritten by Mask & Table
        """
        return NotImplementedError
    
    def has_changed(self, field_name):
        """
        return the value from the widget
        """
        
        if field_name not in self.gui_fields:
            dbg.write("%s Non in gui_fields %s" % (field_name, self.gui_fields.keys()))
            raise sqlkit.exc.FieldNotInLayout("field_name: %s" % (field_name))

        field = self.gui_fields[field_name]
        
        return field.has_changed()

    def record_has_changed(self):
        """
        check if any data has been written in the fields after
        record display. Uses field.has_changed()
        """
        ## this is needed since it's hard to say if an instance has been modified
        ## eg: a new item is added to the session, no editing is done. A reload is issued
        ## I want to avoid the dialog: do you want to save?
        ## session.dirty would (correctly) say a commit is needed

        if not self.current:
            return False

        obj = self.current
        
        for sqlwidget in self.related:
            if sqlwidget.record_has_changed():
                return True

        for field in self.gui_fields:      
            if self.is_mask():
                ## this part is needed only for mask as in table the cell-renderer does it
                ## as soon as you leace the cell
                ## if we setattr now the value in the entry cannot reach the object
                ## My doubt is that we should probably firstly run the validation
                setattr(obj, field.field_name, field.get_value())
            if self.has_changed(field.field_name):
                return True

        return False

    def save_unsaved(self, refresh=True, skip_new=False, skip_check=False, proceed=True):
        """
        Check if it needs saving. In case ask for confirmation and proceed.
        This triggers both session changes *AND* changes to the current mask that
        may not be in the session.

        skip_check: we already know it needs saving. Passed to unsaved_changes_exists
        skip_new: skip_new may be an object whose changes we disregard (see unsaved_changes_exist)
        Return False if cancel is pressed
        """
        response = True
        if self.unsaved_changes_exist(skip_new=skip_new) or skip_check:
            dialog = UnsavedDataDialog(self)
            response = dialog.run()

            if response == gtk.RESPONSE_CANCEL:
                pass

            if response == gtk.RESPONSE_YES:
                if proceed:
                    self.record_save(ask=False)
            
            ## you don't want to save. Let's prevent a delayed commit
            ## we don't need to care about deleted becouse when you delete
            ## the commit is immediate
            if response == gtk.RESPONSE_NO:
                self.discard_changes()
     
        return response

    def discard_changes(self):
        """
        Discard any changes in the session, refreshing all objects
        """
        for obj in self.session.dirty:
            dbg.write("session.refresh(%s)" % obj)
            self.session.refresh(obj)
        for obj in self.session.new:
            dbg.write("session.expunge(%s)" % obj)
            self.session.expunge(obj)
        self.last_new_obj = None  ## FIXME: unsure...
        
    def unsaved_changes_exist(self, skip_new=False, skip_check=False):
        """
        check if session needs committing by looking dirty, deleted and new
        skip_new: skip_new may be an object that we are not interested in saving
                  new object that where not changed but have default values fall here
        """
        # skip_check is passed to Mask.unsaved_changes_exists
        if self.session.dirty:
            for dirty in self.session.dirty:
                if self.session.is_modified(dirty, passive=True):
                    return True
        if self.session.deleted:
            return True

        if self.session.new:
            for obj in self.session.new:
                if obj is skip_new:
                    self.sb(_("Disreguarding new obj"), seconds=3)
                    continue
                if self.session.is_modified(obj, passive=True):
                    return True

        return False
    
###### Validation
    def digits_check_input_cb(self, widget, event):
        """
        prevents the possibility of inputting wrong chars
        """
        key = gtk.gdk.keyval_name (event.keyval)
   
        if key in ('KP_Decimal',) and numbers.get_decimal_symbol() == ",":
            event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
            event.keyval = gtk.keysyms.comma
            event.window = widget.window
            
            widget.emit('key-press-event', event)
            return  True

        KEYPAD_KEYS = '(KP_[0-9]|KP_Add|KP_Decimal|KP_Subtract|comma'
        ONLYDIGITS="%s|[0-9.,]|BackSpace|Left|Right|F1|period|Tab|Up|Down|Return|Esc)"

        if not re.match (ONLYDIGITS % KEYPAD_KEYS, key):
            self.sb(_('Char %s is not accepted in numeric context' % key))
            return True

    def record_validate(self, obj=None, single_fields=True, related=None):
        """
        any validation should live here
        single_fields=bool validation of single fields is done here for table 
                           but in  mask2obj for Masks
                           single_fields determines if check for single fields is done
        returns the validation_error dict to propagate the error info upward
        """
        if not hasattr(self, 'validation_errors') or related:
            self.validation_errors = {}

        if obj is None:
            obj = self.get_current_obj()
            if obj is None:
                return {}


        for sqlwidget in self.related:
            self.validation_errors.update(
                sqlwidget.record_validate(related=sqlwidget.relationship_path))
            
        if single_fields:
            self.record_validate_fields(obj)

        try:
            self.run_hook('on_validation', )
        except exc.ValidationError, e:
            self.handle_validation_errors(e)

        if related:
            return self.validation_errors

        if self.validation_errors: # just one error dialog
            dialog = ValidationErrorDialog(self)
            dialog.run()
            #self.validation_error_dialog()
    
    def handle_validation_errors(self, error=None, field_name=None):
        """
        handle the error raised by a field or take care of action in
        self.validation_error dict and raise exception for record_save
        """
        if not field_name:
            field_name = 'record validation' # a key to be used in self.validation_errors
        
        if not field_name in self.validation_errors:
            self.validation_errors[field_name] = []

        self.validation_errors[field_name] += [error.message]

        self.sb(error.message, seconds=30)

    def record_validate_fields(self, obj):
        """
        validate any fields in self.gui_fields
        """
        for field in self.gui_fields:
            field_name = field.field_name
            try:
                if field.mapper:   # persisted fields, mask2obj has already cleaned  them
                    value = getattr(obj, field_name)
                    self.gui_fields[field_name].validate( value , clean=True)
                else:              # fields only present in the GUI, value is not in obj
                    value = self.gui_fields[field_name].get_value()
                    self.gui_fields[field_name].validate( value , clean=True)

            except exc.ValidationError, e:
                self.handle_validation_errors(e, field_name=field_name)

        
###### Hooks
    def run_hook(self, mode, *args, **kw):
        """
        look for a possible hook and call it.
        mode: the hook type (eg.: set_value, completion...)
        """
        
        if not self.relationship_leader or (self.relationship_leader is self):
            hook_name = "%s" % (mode)
        else:
            hook_name = "%s__%s" % (mode, '__'.join(self.relationship_path))

        sqlwidget = self.relationship_leader or self

        if 'field_name' in kw:
            hook_name += "__%(field_name)s" % kw
            
        if hasattr(sqlwidget, hook_name):
            if 'field_name' in kw:
                return getattr(sqlwidget, hook_name)(kw['field_name'], *args)
            else:
                return getattr(sqlwidget, hook_name)(*args)
    
        
###### Callback
    def clear_cb(self, *args):
        self.clear()

    def reload_cb(self, widget):
        """
        issue a reload operation on master. Call back of reload button
        """
        self.grab_focus(widget)
        try:
            self.reload( )
        except (exc.ValidationError):
            return True

    def record_forward_cb(self):
        """
        it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing
        """
        pass

    def record_back_cb(self):
        """
        it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing
        """
        pass
    
    def delete_event_cb(self, *args):
        """
        Quit operations: check if need to save first
        """
        try:
            self.record_save()
        except (exc.ValidationError, exc.CancelledAction), e:
            print e
            return True
        self.emit('delete-event')
        self.widgets['Window'].destroy()
        self.filter_panel.destroy()
        if self.single:
            self.gquit()
        del self

###### Record browsing 
    def clear(self, widget=None):
        """clear the mask for a new record"""
        pass
    
    def reload(self, sql=None, params=None, limit=None, constraint={},
               reload_constraint=False, display=True, order_by=None):
        """reload data from db

        sql may be a tuple (sql_statement, bind_params) or just a sql_statement
        """
        if limit:
            self.limit = limit

        if order_by:
            self.order_by = order_by
            
        if constraint:
            self.constraint=constraint

#         if sql is None:
#             sql = self.sql

        if isinstance(sql, tuple) and len(sql) == 2:
            sql_str, params = sql
        else:
            sql_str = sql
            params = None

#         if reload_constraint == True:
#             self.sql = (sql_str, params)

        self.session.expunge_all()
        self.last_new_obj = None
        query = self.query.filter(sql_str)
        if params:
            query = query.params(**params)
        if self.order_by:
            query = query.order_by(self.order_by)

        query = self.filter_panel.add_filter_conditions(query)

        if self.limit:
            query = query.limit(self.limit)
                
        if self.is_mask():
            self.current = None
            self.clear(check=False)
        self.records = query.all()
        if display:
            self.record_display(check=False)

        length = len(self.records)
        ## after a reload the transaction will stay opend if session.autocommit=False
        ## in postgres this will be evident by "idle in transaction" state of he process
        ## that will inhibit a number of operation (eg.: altering tables)
        ## FIXME: whe we have m2m relation this is not enought, I open some table
        ## and I don't understand where...
        ## nice info here: http://wiki.dspace.org/index.php/Idle_In_Transaction_Problem
        self.session.rollback()
        return length

    def set_records(self, records):
        """set 'records' as the list of record to manage
        """
        self.records = records
        self.last_new_obj = None
        self.record_refresh()

    def record_refresh(self):
        """to be overloaded: 
        """
        self.emit('records-displayed')
        pass

#     def reload_one(self,field, value):
#         """compact way to view a single record or records with a single property"""

#         sql = "%s = :%s" % (field, field)
#         bind_parameters = {field : value}
        
#         self.reload(  (sql, bind_parameters)  )
    
    def get_new_object(self, session=True):
        """create a new object from the class of the mapper and 
        place it in the session
        """
        new_obj = self.mapper.class_()

        if session:
            self.session.add(new_obj)
        return new_obj

####### Dialog
    def dialog(self, type='ok-cancel', text='', title='', layout=None, icon='gtk-dialog-question'):
        """
        pop a dialog modal and transient, type can be:
        ok, ok-cancel, yes-no, yes-no-cancel, ok-apply-cancel
        text uses markup
        """
        if not layout:
            layout = 'i=%s:6 l=message' % icon
            

        dialog, l = self.lay_obj.dialog(lay=layout, title=title,
                                        type=type, show=False)
        if 'l=message' in l.widgets:
            l.prop(('l=message', 'use_markup', True))
            l.widgets['l=message'].set_text(text)

#         l.widgets['l=a'].set_markup(
#             '<span size="14000">%s</span>' % text)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        return response
    
    def message(self, text='', type='question'):
        self.response = None
        dialog, l = self.lay_obj.message(text=text, type=type)
        #dialog.connect('response', self.response_cb )
        self.response = dialog.run()
        dialog.destroy()
        return dialog
    
    def about_dialog_cb(self, menuItem):
        """
        The about dialog
        """
        self.about_dialog.run()
        self.about_dialog.destroy()
        
    def create_about_dialog(self):
        """
        Create a default AboutDialog
        """
        def func(dialog, link, user_data):
            import webbrowser
            webbrowser.open(link)
            
        about_dialog = gtk.AboutDialog()
        gtk.about_dialog_set_url_hook(func, None)
        about_dialog.set_authors(["Sandro Dentella <sandro@e-den.it>"])
        about_dialog.set_license("GPL v.3")
        about_dialog.set_version(sqlkit.__version__)
        about_dialog.set_name("sqlkit")
        about_dialog.set_website("http://sqlkit.argolinux.org")
        about_dialog.set_website_label("http://sqlkit.argolinux.org")
        return about_dialog
        #dialog.show()
        

###### Misc
    def export(self, menuItem):
        self.dialog(type='ok',
                    text=_("Sorry, export is implemented only for table view"))

    def get_field_type(self, field_name):
        return self.mapper_info.fields[field_name]['type']

    def get_label(self, field_name):
        """
        return field_name translated according to map_label + gettext
        """
        return _(get_label(field_name, layout=self.lay_obj))

    def set_current(self, pk=None):
        """retrieve a record and set it as current
        """
        raise NotImplemented
    def set_format(self, format_dict):
        """
        Set format for each column.
        format_dict: a dictionary whose keys are field_names and values are format
        according to babels numeric and dates format

        No error is raised if a field_name is not represented so that a format_field can be
        reused in different contexts.

        The dict may also hold info for related tables/masks
        """
        if not format_dict:
            return

        for field_name, format in format_dict.items():
            if field_name in self.gui_fields:
                if isinstance(format, tuple):
                    format, locale = format
                    self.gui_fields[field_name].locale = locale

                self.gui_fields[field_name].format = format

        for widget in self.related:
            widget.set_format(format_dict)
            
        
###### Checks
    def is_mask(self, obj=False):
        ## bad way to prevent chicken and eggs import problems 
        from sqlkit.widgets import SqlMask
        if obj == False: ## obj may be an empty str: ''
            obj = self
        return isinstance(obj, SqlMask)
    
    def is_fkey(self, field_name):
        """
        return True if this field is a foreign key
        """
        return bool(self.mapper_info.fields[field_name]['fkey'])

    def is_primary(self, field_name):
        """
        return True if this field is a Primary Key
        """
        return bool(self.mapper_info.fields[field_name]['pkey'])

    def is_loader(self, field_name):
        """
        True if field_name is a loader for a related table
        """
        if field_name not in self.mapper_info.field_list:
            return False
        from  sqlalchemy.orm import properties
        prop = self.mapper_info.fields[field_name]['property']
        if isinstance(prop, properties.PropertyLoader):
            return True
        return False


    def is_string(self, field_name):
        """
        Return true if this field is a String type
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.String))
        return False

    def is_date(self, field_name):
        """
        Return true if this field is  date
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Date))
        return False

    def is_datetime(self, field_name):
        """
        Return true if this field is  datetime
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.DateTime))
        return False

    def is_time(self, field_name):
        """
        Return true if this field is time
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Time))
        return False

    def is_interval(self, field_name):
        """
        Return true if this field is time
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            if issubclass(db_type, (sqltypes.Interval)):
                return True
            elif self.mapper_info.fields[field_name]['type'] is datetime.timedelta:
                return True
        return False

    def is_integer(self, field_name):
        """
        Return true if this field is integer
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Integer))
        return False

    def is_float(self, field_name):
        """
        Return true if this field is float
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Float))
        return False

    def is_numeric(self, field_name):
        """
        Return true if this field is numeric
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Numeric))
        return False



    def is_boolean(self, field_name):
        """
        Return true if this field is  date
        """
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, sqltypes.Boolean)
        else:
            return False

    def is_nullable(self, field_name):
        """
        Return true if this field is  date
        """
        return self.mapper_info.fields[field_name]['nullable']

    def is_editable(self, field_name):
        """
        Return true if this field is  date
        """
        return self.mapper_info.fields[field_name]['editable']

    def is_number(self, field_name):
        """
        Return true if this field is a number 
        """
        py_type = self.mapper_info.fields[field_name]['type']
        if py_type:
            return issubclass(py_type, (int, float, decimal.Decimal))
        else:
            return False

    def is_text(self, field_name):
        """
        Return true if this field is Text or was forced gtk.Text
        """
        try:
            if self.laygen.fields_in_layout[field_name].startswith('TX'):
                return True
        except:
            pass
        db_type = self.mapper_info.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Text))
        return False

    def is_toplevel(self):
        """
        return a boolean indicating if the widget is a toplevel widget
        """
        return 'Window' in self.widgets
    
    def fkey_is_valid(self):
        """
        return True if current editable -if exists- has a value that does not need validation
        """
        pass
    
###### debug
    def show_mapper_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.ShowMapperInfo(self.mapper_info)
        
    def show_widget_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.show_widgets(self.widgets['Window'])
        
    def show_class_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.ShowClassInfo(self) 
        
    def mostra(self, what):
        """
        debug: show all attribute of an object
        """
        if isinstance(what, int):
            obj = self.records[what]
        else:
            obj = what
            
        for attr in self.field_list:
            print attr, getattr(obj, attr)
            
    

    def show_field_info(self, wdg, field_name):
        """
        Pop a dialog to give info on the selected field
        """

        dialog, lay = self.lay_obj.dialog(lay="TVS=info", type='ok', title="Info on %s" % field_name)

        tv = lay.widgets['TV=info']
        model = gtk.ListStore(str, str)
        tv.set_model(model)
        tv.set_property('width-request', 210)
        tv.set_property('height-request', 320)
        
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererText()

        tc1 = gtk.TreeViewColumn(_("Property"), cell1, text=0)
        tc2 = gtk.TreeViewColumn(_("Value"), cell2, text=1)

        tv.append_column(tc1)
        tv.append_column(tc2)
        tv.show_all()
        
        for key in ('table_name', 'name', 'db_type', 'col_spec', 'fkey', 'default',
                    'pkey', 'nullable', 'editable', 'length'):
            if key == "db_type":
                model.set(model.append(), 0,  key, 1, self.mapper_info.fields[field_name][key].__name__)
            else:
                model.set(model.append(), 0,  key, 1, self.mapper_info.fields[field_name][key])

        try:
            cell = self.tvcolumns[field_name].get_cell_renderers()[0]
            model.set(model.append(), 0,  'width', 1, cell.get_data('width'))
        except:
            pass

        try:
            model.set(model.append(), 0,  'format', 1, self.gui_fields[field_name].format)
        except:
            pass

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        
        
    def session_show(self, k=None):
        """just for debugging 
        """
        l = []
        j = 0
        for obj in self.session:
            if k is not None:
                print "%.2d %s %s" % (j, obj, hex(id(obj)))
            l += [(hex(id(obj)), obj)]
            j += 1

        l += [('dirty', self.session.dirty)]
        l += [('new', self.session.new)]
        l += [('delete', self.session.deleted)]
        if k is None:
            return l
        else:
            return l[k]
        
    def record_show_changes(self):
        if self.record_has_changed():
            for field in self.gui_fields:
                if field.has_changed():
                    print "OLD: %s   NEW: %s" % (field.initial_value, field.get_value())
                    
###### printing  --  very old code - Not used at the present time
    def printing(self):
        """this will pop entries in the print setup to allow for printing
        A mask will be printed only if a template (.sxw) is provided
        in one of these two ways:
        1. directly set self.print_template pointing to a .sxw file
        2. directly set self.print_template_dir pointing to a directory where
                    many possible templates are.
        3. setting a global dir sqlkit.set_template_dir(). In this case a
                    template will be searched for in a subdir named self.nick

        When a tempate is found the name of the template is stripped of the
        trailing suffix .sxw and that name is used as entry for the menu
        """
        
        Menu = self.widgets['M=file']
        Item = gtk.ImageMenuItem('gtk-print')
        Menu.insert(Item, 2)
        SubMenu = gtk.Menu()
        Item.set_submenu(SubMenu)

        Item.connect('activate', self.print_fill_submenu, SubMenu)
        Menu.show_all()

        #Item1 = gtk.MenuItem('template 1')
        #SubMenu.append(Item1)
    
    def print_fill_submenu(self, item, sub):
        return
        try:
            a = self.printing_menu_filled
            return
        except:
            pass
        
        # check if a printing sistem is there
        templates, template_dir = self.get_templates()

        for template in templates:
            for format in template[1]:
                item = gtk.MenuItem("%s - %s" % (template[0], format))
                item.connect('activate', self.print_file, template[2], format)
                sub.append(item)

        if not templates:
            item = gtk.MenuItem("No templates for nick '%s' in %s" %
                                (self.nick.replace('_','__'), template_dir) )
            sub.append(item)
            
        sub.show_all()
        self.printing_menu_filled = True
                
    def get_templates(self):
        "return a list of tuples (name.sxw, entry name) for each template found"

        filenames = []
        try:
            template = self.print_template
            self.template2tuple(template, filenames)
        except:
            pass

        template_dir = ""
        try:
            template_dir = self.print_template_dir
        except:
            try:
                template_dir = print_template_dir
            except:
                pass

        if template_dir:

            ## look for a subdir self.nick, this may fail becouse you didn't
            ## define the nick or becouse there is no foulder

            for d in os.listdir(template_dir):
                if d == self.nick:
                    path = os.path.join(template_dir, d)
                    if os.path.isdir(path):
                        ## here are the templates for us
                        for f in os.listdir(path):
                            self.parse_template_and_add(f, filenames, path)

        return (filenames, template_dir)
    
    def parse_template_and_add(self, template, filenames, path=None):
        """check if it is a file, it not just returns. Otherwise check the
        name to see:
        1. if it ends with .sxw (otherway it returns)
        2. which is the name to use in t menu_entry
        3. if it has sxw or pdf in the name, thus suggesting which transformation
           are allowed. Defaults to just pdf.

           eg: test.sxw  (just pdf output, menu entry 'test')
               my_test_pdf_sxw.sxw  (both output allowed, menu entry: 'my test')
                          note that _ was transformed in space.

        an attempt to further translate the resulting entry is made against
        layout.set_description_fields

        """
        if path:
            template = os.path.join(path, template)

        if not os.path.isfile(template):
            return
        
        formats = []
        base = os.path.basename(template)
        p = re.compile(r"""
            ^(?P<name>.+?)                   # the real name, non greedy fashion
            (_(?P<format>(_?pdf|_?sxw)*))?   # output format encoded
            \.sxw$                           # the extension
        """, re.VERBOSE)
        m = p.match(base)
        if m:
            name = m.group('name')
            name = layout.get_label(name)
            name = name.replace('_', ' ')
            try:
                formats = m.group('format').split('_')
            except:
                formats = m.group('format')
            if formats is None:
                formats = ['pdf']

            filenames.append((name, formats, template))
            
    def print_file(self, item, template, format):

        from ooffice import opop
        import subprocess
        
        page = opop.Sxw(file=template)
        #page.verbose = True
        #ret = self.actions.on_print(page)
        if ret is not True :
            self.message(type='warn', text=_("Missing data"))
            return

        outfile = page.make(format=format)
        if isinstance(outfile, list):
            outfile = outfile[0]
        if sys.platform.startswith('linux'):
            if format.startswith('pdf'):
                try:
                    subprocess('acroread %s' % outfile)
                except:
                    try:
                        os.system('gv %s' % outfile)
                    except:
                        try:
                            os.system('xpdf %s' % outfile)
                        except:
                            pass
                        
            elif format == 'sxw':
                os.system('ooffice %s' % outfile)
            
        else:
            os.startfile(outfile)
        page.clean()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.tables)

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.tables)


def set_template_dir(dir):
    global print_template_dir
    print_template_dir = dir


class UnsavedDataDialog(object):
    """
    A dialog that allows to see which data have been modifiedx
    """
    def __init__(self, master):
        self.master = master
        general_msg = [_("Save unsaved data?")]
        layout = "{v { i=gtk-dialog-question:6 l=msg}  {>.details TVS=details} }"
        
        self.dialog, l = master.lay_obj.dialog(title=_("Unsave data"),
            type='yes-no-cancel', text="\n".join(general_msg),  lay=layout)

        tv = l.widgets['TV=details']
        expander = l.widgets['X.details']
        self.model = gtk.TreeStore(str, str, str, str)
        tv.set_model(self.model)
        tv.set_property('width-request', 600)
        tv.set_property('height-request', 150)
        
        cell0 = gtk.CellRendererText()
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererText()
        cell3 = gtk.CellRendererText()

        tc0 = gtk.TreeViewColumn(_("State"),     cell0, markup=0)
        tc1 = gtk.TreeViewColumn(_("Field name"), cell1, markup=1)
        tc2 = gtk.TreeViewColumn(_("Original value"), cell2, markup=2)
        tc3 = gtk.TreeViewColumn(_("Present value"), cell2, markup=3)

        tv.append_column(tc0)
        tv.append_column(tc1)
        tv.append_column(tc2)
        tv.append_column(tc3)
        tv.show_all()

        self.fill_model()

        self.dialog.show_all()

    def run(self):
        response = self.dialog.run()
        self.dialog.destroy()
        return response

    def fill_model(self):
        
        """
        Dialog to allow analysis of changed data
        """
        from sqlkit.db import utils 
        if self.master.is_mask():
            try:
                self.master.record_mask2obj(self.master.get_current_obj())
            except Exception, e:
                exc.ValidationError(e.message)

        if self.master.session.dirty or (
            self.master.record_has_changed() and self.master.current not in self.master.session.new):
            dirty_iter = self.model.append(None)
            self.model.set(dirty_iter, 0, '<b>%s</b>' % _('Modified'))

            for item in self.master.session.dirty:
                for field_name, old, new in utils.get_differences(item, self.master.session):
                    if not field_name in self.master.gui_fields:
                        continue
                    field = self.master.gui_fields[field_name]

                    iter = self.model.append(None)
                    self.model.set(iter,
                                   0, "<i>%s</i>" % utils.clean_for_markup(item)[:25],
                                   1, "%s" % self.master.get_label(field_name),
                                   2, old and utils.clean_for_markup(field.get_human_value(old)) or '',
                                   3, new and utils.clean_for_markup(field.get_human_value(new)) or '',
                                   )

        if self.master.session.deleted:
            deleted_iter = model.append(None)
            self.model.set(dirty_iter, 0, '<b>%s</b>' % _('Deleted'))
            for item in self.master.session.deleted:
                iter = self.model.append(None)
                self.model.set(iter,
                               2, "%s" % item)
                
                
        if self.master.session.new:
            new_iter = self.model.append(None)
            self.model.set(new_iter, 0, '<b>%s</b>' % _('New'))
            for item in self.master.session.new:
                iter = self.model.append(None)
                self.model.set(iter,
                               3, "%s" % item.__class__.__name__)
                
                




class ValidationErrorDialog(object):

    def __init__(self, master):
        """
        represent the errors in self.validation_errors and raise ValidationError
        to correctly propagate the error upwards
        """
        self.master = master
        general_msg = _('Errors are present in the record. \nCorrect them now, to continue \nor delete the record')
        

        layout = """i=gtk-dialog-error:6 l=general:<
                    TVS=details -"""
        
        self.dialog, lay = master.lay_obj.dialog(lay=layout, type='ok',
                                          title=_("Validation errors"))
        lay.widgets['l=general'].set_text(general_msg)
        
        tv = lay.widgets['TV=details']
        model = gtk.ListStore(str, str)
        tv.set_model(model)
        tv.set_property('width-request', 420)
        tv.set_property('height-request', 150)
        
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererText()

        tc1 = gtk.TreeViewColumn(_("Field name"), cell1, markup=0)
        tc2 = gtk.TreeViewColumn(_("Error"), cell2, markup=1)

        tv.append_column(tc1)
        tv.append_column(tc2)
        tv.show_all()

        self.fill_model(model)
        self.dialog.show_all()

    def run(self):
        response = self.dialog.run()
        self.dialog.destroy()

        self.master.validation_errors = {}
        raise exc.ValidationError

    def fill_model(self, model):
        """
        Fill the model of the treeview that presents the validation errors
        """

        for key in (self.master.validation_errors.keys()):
            for i, err in enumerate(self.master.validation_errors[key]):
                iter = model.append(None)
                if i == 0:
                    model.set(iter, 0, "<b>%s</b>" % _(get_label(key, layout=self.master.lay_obj)))
                model.set(iter, 1, "<i>%s</i>" % err)
            
#     def fill_model(self):
#         self.master.validation_error_fill_model(model)        
    


