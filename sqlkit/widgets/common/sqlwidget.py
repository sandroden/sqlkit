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
from sqlkit.layout import map_labels
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
from sqlkit.db import minspect
from sqlkit.widgets.common import completion
from sqlalchemy.orm import attributes
from sqlkit.misc.utils import Container
import sqlkit
from sqlkit import _

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
        }

    fields   = None  # fields to use (InspectMapper)
#    tables = None    # Table objects referenced as foreign keys
    values = None    # real value for foreign key
                     # (when lookup is displeyed instead)
#    __metaclass__ = dbg.LogTheMethods
#    __metaclass__ = misc.autoreload.MetaAutoReloader
    records = None
    last_new_obj = None
    def __init__ (self, mapper=None,
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
                  Class=None,
                  join=None,
                  ro=False,
                  noup=[],
                  sql=None,
                  constraint={},
                  dbproxy = None,
                  order_by=None,
                  limit=200,
                  field_list=None,
#                  filter=True,
                  session=None,
                  metadata = None,
                  ignore_fields = None,
                  hide_fields = None,
                  ## more
                  single=False,
                  nick=None,
                  about_dialog = None,
#                  actions=None,
                  dev=False,
                  xml=False,
                  relationship_mode = 'SINGLE',
                  relationship_path = None,
                  relationship_leader = None,
                  format=None,
                  label_map = None,
                  ):
        """create an interface and allow to save/store data from a database

        layout:    a layout describing the desired layout (see layout package)
#        actions: a validator to be used to validate fields and records
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
        Class:  an instrumented class (one connected o a mapper). This along with
                session may be the only parameters
        table[s]: a table name. The plural is left for a possibe extensions to automatic join
        mapper: a sqlalchemy mapper. a Class is built runtime, metadata is read from local_table
        session: the session where to put all data.

        relationship_mode: SINGLE, m2m, m2o, o2m
        relationship_path: the path needed to join two tables. See sqlalchemy on 'quering
                  with joins'. Used by filter_panel to setup join condition when filtering
                  when relationship_mode is not SINGLE. May be a list or a string:
                  'genres', 'director nationality', ['director','nationality']
        relationship_leader: the main sqlmask (sqltable) that "owns" the filter_panel
        format: a format dict as for set_format, settings formatting info for numbers and dates
        """
        gobject.GObject.__init__(self)
        self.related = Container()
        self.vfields = Container()
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
        self.mapper = self.get_mapper(mapper, table or tables, Class)
        self.metadata = self.get_metadata(metadata, self.mapper)
        ## we can use singular or plural as an option, plural in the code
        if table and not tables:
            tables = table
        self.tables = self.get_table(tables)
        self.nick= self.get_nick(nick)
        self.ro = ro
        self.noup = noup
        self.rows = rows
        self.hidden_field = hide_fields
        self.fields = self.get_fields()
        self.field_list = self.parse_fields(field_list, layout)
        self.ignored_fields = self._set_ignored_fields(ignore_fields)
        if hide_fields:
            self.hide_fields()
        self.title = self._get_title(title)
#        self.tables = {}
        self.values = {}
        ## create the interface and add obvious constraints
        self.naked = naked
        self.lay   = layout
        self.sql   = sql
#        self.sqlData = sqldata.SqlData(None, self.fields, self.session)
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
            
    def show(self, show):
        """create the widget and go on displaying the layout
        """
        self.lay_obj, self.widgets  = self._get_layout(self.lay, self.naked,)
#         if self.sql or isinstance(self, sqlkit.table.SqlTable):
#             self.reload(self.sql, limit=self.limit)
            
        ## only render when dimentions are complete
        #self.widgets['Window'].show()
        lcontainer_name = self.lay_obj.container().el_def
        el_def = re.sub(':.*','', lcontainer_name)
        #dbg.write('lcontainer_name: ', el_def)
        if show:
            self.widgets[el_def].show()
        
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
        
    def get_session(self, session):
        if session:
            return session
        else:
            return self.dbproxy.get_session()
    
    def get_mapper(self, mapper, tables, Class=None):

        if mapper:
            return mapper
        elif Class:
            mapper = class_mapper(Class)
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
                get_the_keys = self.fields.all_keys
            else:
                get_the_keys = self.fields.keys
                
            if self.dev:
                new_field_list = get_the_keys()
            else:
                ## I want all fields not ending with _id
                ## *AND* all fields that REFERENCE other keys
                ## i.e.: if you have city_id that references a city I want
                ## to see it, but I don't want to see a sequence normally.
                new_field_list = [f for f in get_the_keys()
                          if not f == 'id' or self.fields[f]['fkey'] ]

            
        else:
            if isinstance(field_list, str):
                new_field_list = [f for f in re.split('[ ,]+',field_list) if f]
            else:
                new_field_list = field_list
        return new_field_list
    
    def get_actions(self, actions):
        if not actions:
            actions = Actions()
        actions.master = self
        return actions
    
    def get_nick(self, nick):
        if not nick:
            if self.tables:
                nick = self.tables
            else:
                nick = self.mapper.tables[0].name
        return nick
            
#     def get_engine(self, engine, mapper):
#         if not engine:
#             if mapper:
#                 dbg.write(mapper)
#                 engine = mapper.local_table.engine
#             else:
#                 try:
#                     engine = schema.default_metadata.engine
#                 except:
#                     msg = "You may want to use globalconn when creating engine"
#                     raise MissingEngine(msg)
                
#         return engine
    
    def get_fields(self):
        """Fields is a dictionary with info on the fields derived from the
        db via the mapper (inspecting it)
        """
        return minspect.InspectMapper(self.mapper, noup=self.noup, ro=self.ro)
        
    def _get_layout(self, lay, naked):
        """lay may be a definition string or another SqlMask in case the layout has
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
        self.layout = lay
        self.lay_obj = layout.Layout(self.layout, addto=self.addto,
                                     title=self.title, opts='T-', label_map=self.label_map)
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

        if 'Window' in self.lay_obj.elements:
            self.lay_obj.connect(('Window', 'delete_event', self.delete_event))
            if self.geom:
                self.resize(*self.geom)

        if self.is_mask():
            self._add_click_for_filter()
            self._add_color_to_labels()


        self.setup_field_validation()
        self._add_actions_to_buttons()
        self._fill_menubar_menu()
        self.add_accelerators()
        return (self.lay_obj, self.widgets)
    
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
        
    def _get_filter_panel(self):
        if self.relationship_leader:
            return self.relationship_leader.filter_panel
        
        return sqlfilter.FilterPanel(self, visible=False)

    def add_accelerators(self):
        """Add accelerators: now Ctrl-h, Ctrl-q"""

        # key accelerators
        if self.addto:
            return
        
        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_group(ord('h'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.show_widget_info)
        self.accel_group.connect_group(ord('q'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.gquit)
        self.widgets['Window'].add_accel_group(self.accel_group)
            
        
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save-as'       : self.record_save_new,
            'tb=gtk-save'       : self.record_save_cb,
            'tb=gtk-new'        : self.record_new,
            'tb=gtk-delete'     : self.record_delete,
            'tb=gtk-refresh'    : self.reload_cb,
            'tb=gtk-quit'       : self.delete_event,
            'tb=gtk-go-forward' : self.record_forward,
            'tb=gtk-go-back'    : self.record_back,

            ## in case the programmers has set them
            'b=gtk-save-as'       : self.record_save_new,
            'b=gtk-save'       : self.record_save_cb,
            'b=gtk-new'        : self.record_new,
            'b=gtk-delete'     : self.record_delete,
            'b=gtk-refresh'    : self.reload_cb,
            'b=gtk-quit'       : self.delete_event,
            'b=gtk-go-forward' : self.record_forward,
            'b=gtk-go-back'    : self.record_back,
            }
        for widget_name, handler in actions.iteritems():
            if widget_name in self.widgets:
                #print "_add_actions_to_button: %s %s %s" % (
                #    widget_name, 'clicked', handler)
                #self.widgets[widget_name].connect('clicked', handler)
                self.lay_obj.connect((widget_name, 'clicked', handler))
                #self.lay_obj.tooltips.set_tip(self.widgets[widget_name], "mmh")
                #self.lay_obj.tip(widget_name, "mi chiamo %s" % widget_name)

        ## style for toolbar if any
        if 'O.tool' in self.widgets:
            self.widgets['O.tool'].set_show_arrow(False)
            self.lay_obj.prop('O.tool', 'toolbar_style','GTK_TOOLBAR_ICONS')
    
        if 'O.quit' in self.widgets:
            self.widgets['O.quit'].set_show_arrow(False)
            self.lay_obj.prop('O.quit', 'toolbar_style','GTK_TOOLBAR_ICONS')

        if 'm=modify' in self.widgets:
            self.lay_obj.menu('m=modify',
                              ('gtk-delete', 'activate', self.record_delete),
                              ('gtk-refresh', 'activate', self.reload_cb),
                              )

####### Saving
    def record_delete(self, widget=None):
        """invokes the validator before DELETing a record"""
        pass
    
    def record_save_cb(self, ev):
        """Save the record and invokes the validator before UPDATE/INSERT a record
        """
        try:
            self.record_save()
        except sqlkit.exc.CancelledAction:
            pass
    
    def record_save_new(self, ev):
        """Save the record as a new record, ie letting pk not be set 
        """
        raise NotImplementedError

    def commit(self):
        if self.ro:
            return
        try:
            self.session.commit()
        except exceptions.SQLError, e:
            self.SQLErrorHandler(e)
            dbg.write("Exception: %s" % e.orig) 
            #self.message(str(e.orig))
            self.session.rollback()
            raise sqlkit.exc.CommitError
            
    def SQLErrorHandler(self, e):
        # TIP: message in the status bar when a commit error is handled
        self.message(type='error',
                     text=_("%s - Dirty objects: %s - New objects: %s") % \
                     (str(e.orig),len(self.session.dirty),len(self.session.new)))
        self.sb(e.orig)
        dbg.write("Scritto %s su sb" % (e.orig))

    def record_validate(self, obj, mode, constraint={} ):
        """any validation should live here

        constraint: this is a dictionary of values that are enforced.
        
        Constraints are applied *after* path2dict handling and before
        actions.on_update / actions.on_insert

        """
        ## FIXME: vars(obj) means nothing...
        rdict = vars(obj)
        ## Applying constraint *after* check that I inserted something
        if constraint:
            self.constraint=constraint

        if mode == 'INSERT':
            pass
            #self.actions.on_insert(new=obj)
            #dbg.write("INSERTING record", rdict)
            #self.sqlData.add(rdict)

        elif mode == 'UPDATE':
            pass
            #self.actions.on_update(new=obj)
            #self.sqlData.set(rdict, index=int(self.model_path))
            #self.sqlData.current = self.path2sqldata_index(self.model_path)
            #self.sqlData.set(rdict)
        pass
    
    def handle_validation_error(self, error):
        """
        handle the error raised by a field
        """
        self.sb(error.message)
            

####### Record browsing 
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

        self.session.clear()
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
            self.record_display()

        length = len(self.records)
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

    def reload_one(self,field, value):
        """compact way to view a single record or records with a single property"""

        sql = "%s = :%s" % (field, field)
        bind_parameters = {field : value}
        
        self.reload(  (sql, bind_parameters)  )
    
    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        self.reload( )

    def record_forward(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass

    def record_back(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass
    
    def get_new_object(self, session=True):
        """create a new object from the class of the mapper and 
        place it in the session
        """
        new_obj = self.mapper.class_()

        if session:
            self.session.add(new_obj)
        return new_obj

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
        
    def get_differences(self, obj):
        """show differences between old and new version of an object
        """
        msg = []
#        for field_name in self.mapper.columns.keys():
        for field_name in self.field_list:
            #print "FIELD_LIST", self.field_list
            new = None
            try:
                field_name_transated = _(get_label(field_name, layout=self.lay_obj))
                new, unchanged, old =  attributes.get_history(
                    attributes.instance_state(obj), field_name_translated)
                #print "%s:: new: %s - unchanged: %s - old: %s" % (field_name, new, unchanged, old)
            except:
                pass
            if new:
                msg += ["%s: %s -> %s" % (field_name, old, new)]
        return "\n".join(msg)

    def has_changed(self, field_name):
        """return the value from the widget
        """
        
        if field_name not in self.vfields:
            dbg.write("%s Non in vfields %s" % (field_name, self.vfields.keys()))
            raise sqlkit.exc.FieldNotInLayout("field_name: %s" % (field_name))

        field = self.vfields[field_name]
        
        return field.has_changed()

    def record_has_changed(self):
        """check if any data has been written in the fields after
        record display. Uses field.has_changed()
        """
        ## this is needed since it's hard to say if an instance has been modified
        ## eg: a new item is added to the session, no editing is done. A reload is issued
        ## I want to avoid the dialog: do you want to save?
        ## session.dirty would (correctly) say a commit is needed

        
        for field_name in self.field_list:      
            try:
                changed = self.has_changed(field_name)
            except sqlkit.exc.FieldNotInLayout:
                continue

            if changed:
                return True

        return False

    def get_pk(self):
        """
        return the pkeys of the primarytable
        """
        return self.fields.pkeys[self.fields.get_primary_table()]

    def get_value(self, field_name):
        """
        to be overwritten by Mask & Table
        """
        return NotImplementedError
    
####### Validation
    def digits_check_input_cb(self, widget, event):
        """prevents the possibility of inputting wrong chars"""
        ## fixme: missing comma, and cut&paste
        key = gtk.gdk.keyval_name (event.keyval)
        #dbg.write(key)
        ONLYDIGITS="([0-9.,]|BackSpace|Left|Right|F1|period|Tab|Up|Down)"
        if not re.match (ONLYDIGITS, key):
            #dbg.write("key: %s" % key)
            return True
#     def record_display(self, record=None, incr=0):
#         self.actions.on_record_display()
        

####### Dialog
    def dialog(self, type='ok-cancel', text='', title='', layout="l=a"):
        """
        pop a dialog modal and transient, type can be:
        ok, ok-cancel, yes-no, yes-no-cancel, ok-apply-cancel
        text uses markup
        """
        dialog, l = self.lay_obj.dialog(lay=layout, title=title,
                                        type=type, show=False)
        if layout == 'l=a':
            l.prop(('l=a', 'use_markup', True))
            l.widgets['l=a'].set_text(text)
            
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
        

####### Misc
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
        self.widgets['Window'].resize(width, height)
        
    def set_fkey_value(self, field_name, value):
        """needed for completion, to set real value when
        description is shown instead
        """
        pass
    
    def delete_event(self, *args):
        """Quit operations: check if need to save first """

        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)

        if not self.save_unsaved():
            return

        self.widgets['Window'].destroy()
        self.filter_panel.destroy()
        if self.single:
            self.gquit()

    def save_unsaved(self, refresh=True, skip_check=False):
        """check if it needs saving. In case ask for confirmation and proceed.
        This triggers both session changes *AND* changes to the current mask that
        may not be in the session.

        skip_check: we already know it needs saving. Passed to unsaved_changes_exists
        Return False if cancel is pressed
        """

        if self.unsaved_changes_exist(skip_check=skip_check):
            msg = [_("Save unsaved data?")]
            if self.session.dirty:
                #dbg.write("unsaved", self.session.dirty)
                msg += [_('unsaved: %s') % (len(self.session.dirty))]
                msg += [self.get_differences(o) for o in self.session.dirty]
            if self.session.new:
                msg += [_('new: %s') % (len(self.session.new))]

            response = self.dialog(type='yes-no-cancel', text="\n".join(msg))
                                   
            if response == gtk.RESPONSE_CANCEL:
                #dbg.write("Response CANCEL")
                return False

            if response == gtk.RESPONSE_YES:
                #dbg.write("Response YES")
                self.session.commit()
                self.last_new_obj = None

            ## you don't want to save. Let's prevent a delayed commit
            ## we don't need to care about deleted becouse when you delete
            ## the commit is immediate
            if response == gtk.RESPONSE_NO:
                #dbg.write("RESPONSE NO")
                if refresh:
                    for obj in self.session.dirty:
                        dbg.write("session.refresh(%s)" % obj)
                        self.session.refresh(obj)
                    for obj in self.session.new:
                        dbg.write("session.expunge(%s)" % obj)
                        self.session.expunge(obj)
                    self.last_new_obj = None  ## FIXME: unsure...
                else:
                    dbg.write("refresh:", refresh)
                dbg.write(self.session.dirty)
     
        return True

    def unsaved_changes_exist(self, skip_check=False):
        """
        check if session needs committing by looking dirty, deleted and new
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
                if self.session.is_modified(obj, passive=True):
                    return True

        return False
    
    def gquit(self, *args):
        gtk.main_quit()
                       
    def sb(self, text):
        """
        write on the status bar, if present
        """

        if self.relationship_leader:
            self.relationship_leader.sb(text)
        else:
            try:
                self.lay_obj.sb(text)
            except Exception, e:
                #print e, vars(e)
                pass

    def _get_title(self, title=None):
        if not title:
            try:
                title=self.table
            except:
                title= self.fields.get_primary_table()
        return title
    
    def add_filter_cb(self, event=None, visible=True):
        """
        Pop a Filter Panel, called from menu item
        """

        self.filter_panel.w['Window'].present()

    def add_filter(self, **kw):
        self.filter_panel.add_filter(**kw)
        
    def show_mapper_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.ShowMapperInfo(self.fields)
        
    def show_widget_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.show_widgets(self.widgets['Window'])
        
    def show_class_info(self, *args):
        from sqlkit.debug import gtk_dbg
        gtk_dbg.ShowClassInfo(self) 
        
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.widgets:
            self.lay_obj.menu(
                'm=file',
                # meu entry to pop filter tool
                (_('Filter panel'),  'activate', self.add_filter_cb),
                ('-', None),
                ('gtk-new', 'activate',  self.record_new),
                ('gtk-save', 'activate',  self.record_save),
                ('gtk-save-as', 'activate',  self.record_save_new),
                ('-', None),
                (_('Export'), 'activate', self.export),
                
                ('gtk-quit', 'activate', self.delete_event)
                )
            self.lay_obj.menu(
                'm=help',
                ('gtk-about', 'activate', self.about_dialog_cb),
                )
            self.lay_obj.menu(
                'm=tools',

                (_('Inspect tables'), 'activate',  self.show_mapper_info),
                (_('Inspect widgets'), 'activate', self.show_widget_info),
                (_('Inspect class'), 'activate', self.show_class_info),

                )
            self.printing()
    def clear_cb(self, *args):
        self.clear()

    def export(self, menuItem):
        self.dialog(type='ok',
                    text=_("Sorry, export is implemented only for table view"))

    def is_fkey(self, field_name):
        """
        return True if this field is a foreign key
        """
        return bool(self.fields[field_name]['fkey'])

    def is_primary(self, field_name):
        """
        return True if this field is a Primary Key
        """
        return bool(self.fields[field_name]['pkey'])

    def is_loader(self, field_name):
        """
        True if field_name is a loader for a related table
        """
        if field_name not in self.fields:
            return 
        from  sqlalchemy.orm import properties
        prop = self.fields[field_name]['property']
        if isinstance(prop, properties.PropertyLoader):
            return True
        return False


    def is_string(self, field_name):
        """
        Return true if this field is a String type
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.String))
        return False

    def is_date(self, field_name):
        """
        Return true if this field is  date
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Date))
        return False

    def is_datetime(self, field_name):
        """
        Return true if this field is  datetime
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.DateTime))
        return False

    def is_time(self, field_name):
        """
        Return true if this field is time
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Time))
        return False

    def is_interval(self, field_name):
        """
        Return true if this field is time
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            if issubclass(db_type, (sqltypes.Interval)):
                return True
            elif self.fields[field_name]['type'] is datetime.timedelta:
                return True
        return False

    def is_integer(self, field_name):
        """
        Return true if this field is integer
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Integer))
        return False

    def is_float(self, field_name):
        """
        Return true if this field is float
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Float))
        return False

    def is_numeric(self, field_name):
        """
        Return true if this field is numeric
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Numeric))
        return False



    def is_boolean(self, field_name):
        """
        Return true if this field is  date
        """
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, sqltypes.Boolean)
        else:
            return False

    def is_nullable(self, field_name):
        """
        Return true if this field is  date
        """
        return self.fields[field_name]['nullable']

    def is_editable(self, field_name):
        """
        Return true if this field is  date
        """
        return self.fields[field_name]['edit']

    def is_number(self, field_name):
        """
        Return true if this field is a number 
        """
        py_type = self.fields[field_name]['type']
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
        db_type = self.fields[field_name]['db_type']
        if db_type:
            return issubclass(db_type, (sqltypes.Text))
        return False


    def get_field_type(self, field_name):
        return self.fields[field_name]['type']

    def set_current(self, pk=None):
        """retrieve a record and set it as current
        """
        raise NotImplemented
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
            
    def is_mask(self, obj=False):
        ## bad way to prevent chicken and eggs import problems 
        from sqlkit.widgets import SqlMask
        if obj == False: ## obj may be an empty str: ''
            obj = self
        return isinstance(obj, SqlMask)
    
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
            if field_name in self.vfields:
                if isinstance(format, tuple):
                    format, locale = format
                    self.vfields[field_name].locale = locale

                self.vfields[field_name].format = format

        for widget in self.related:
            widget.set_format(format_dict)
            
        
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
                    'pkey', 'nullable', 'edit', 'length'):
            if key == "db_type":
                model.set(model.append(), 0,  key, 1, self.fields[field_name][key].__name__)
            else:
                model.set(model.append(), 0,  key, 1, self.fields[field_name][key])

        try:
            model.set(model.append(), 0,  'format', 1, self.vfields[field_name].format)
        except:
            pass

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        
####### printing
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

####### More
def set_template_dir(dir):
    global print_template_dir
    print_template_dir = dir

