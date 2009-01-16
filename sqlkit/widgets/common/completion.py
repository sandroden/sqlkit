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

"""
autocompletion
---------------

``my_sqlwidget.completions.my_field.autostart = n``
(Where n holds the number of chars entered to trogger automatic start of completion)

group_by
--------

``my_sqlwidget.completions.my_field.group_by = field_name``
``field_name`` will be added to the request and used to group completion possibilities 

"""


import re
import gtk
from sqlkit import debug as dbg, _
import sqlkit
from sqlalchemy import text, select, Table
from sqlalchemy.sql import and_, or_, not_
from sqlkit.db.proxy import table2mapper
from sqlkit.db.utils import tables, get_description, DictLike
from sqlkit.exc import *
from sqlkit.db.django_syntax import django2sqlalchemy, path2join
from copy import copy

####### Completion
# EntryCompletion widgets are added on the fly triggered by F1, C-F1 or menu items
# select_values will get data from the db and fill a listore
# match_function filters using re.search from the listore to fill in the completion
#
OP = {
    'sqlite' : 'LIKE',
    'postgres'     : '~*',
    'mysql'  : 'ILIKE',
    }

class SimpleCompletion(object):
    __metaclass__ = dbg.LogTheMethods
    autostart = False
    autostart_last_length = 0
    
    VALUE_COL = 0
    DESCRIPTION_COL = 0
    MARKUP_COL = 0
    OBJ_COL = 1
    MATCH_COL = 2
        
    def __init__(self, master, widget, field_name):

        """completion is the way we can find possible completions of text in
        a cell.  In case the edited field has a Foreign Key constraint
        completion will follow the table/field to retrieve the possible
        values, in case we don't have an fk, completion will suggest values
        already present in the db.

        A completion must be 'requested' (is only issued on demand), unless
        autocompletion is set to n (chars inputted after which it starts). Normal
        bindings are F1 Shift_Enter, Control_Enter or right-click and will 
        fill the gtk.EntryCompletion associated to the entry with values
        accordingly.

        Bindings are set in SqlText inside text_editing_started_cb
        while in SqlMask inside miniwidgets (actually only VarcharWidget and FKeyWidget)

        widget.connect('button-press-event',self.completion.keypress_event_cb,  self.field_name)

        It requires quite a lot of object be already setup in the master
        (actually SqlMask or SqlTable?)
        self.master.fields: an InspectMapper Object
        self.master.engine
        self.master.lay_obj a Layout object (for the tooltips method)
        self.master.mapper
        self.master.values in case of an id, completion will substitute it
             with a description field, for the user benefit. The real value
             of the field will be hold there.
        self.master.vfields (mask wdgets): the mapping field_name -> widget
        
        """


        self.master = master
        self.lookup_values = {}
        self.MATCH_OPERATOR = OP[self.master.metadata.bind.name] or 'LIKE'
        self.widget = widget
        self.field_name = field_name
        self.completion = self.prepare_completion()
        self.column = self.master.fields[field_name]['col']
        self.table = self.column.table
        self.format = get_description(self.table, attr='format')
        self.description = tables[self.table.name].description
        self.attrs = tables[self.table.name].attrs
#        self.columns = [self.master.fields[field_name]['col'] for field_name in self.attrs]
        self.columns = [self.master.fields[self.field_name]['col']]
#        self.attrs = tables[self.table.name].attrs
        self._group_by = None
        self._filter = None
        self.mapper = self.master.mapper # used to track path relationship
        self.from_obj = None
        
    def set_group_by(self, field_name):
        """if group_by is not already in table.attrs, add it runtime
        """
        if not field_name in self.attrs:
            self.attrs += [field_name]
            self.columns = [self.table.columns[name] for name in self.attrs]
        self._group_by = field_name
        
    def get_group_by(self):

        return self._group_by

    def get_entry(self):
        return self.widget

    group_by = property(get_group_by, set_group_by)
    entry    = property(get_entry)

    def prepare_completion(self):
        """
        Prepare an EntryCompletion suitable for... sqlcompletion
        """

        completion = gtk.EntryCompletion()
        completion.set_property('popup-set-width', False)
        completion.set_property('minimum-key-length', 0)
#        completion.set_property('popup-single-match', False)   ???
        completion.connect('match-selected', self.match_selected_cb, self.field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)

        completion.add_attribute(renderer, 'markup', self.MARKUP_COL)

        ## we match against the description field
        ## from the reference docs:
        # The match function is used by the entry completion to determine
        # if a row of the associated tree model should be in the completion list
        completion.set_match_func(self.match_func)
        self.model = self.prepare_model()
        completion.set_model(self.model)
        
        return completion

    def prepare_model(self):
        return gtk.ListStore(str, object, bool)
    
    def add_completion(self, entry):
        """ add a completionEntry to an Entry
        """
        entry.set_completion(self.completion)

    def add_callbacks(self, entry):
        entry.connect('button-press-event', self.pop_menu,  self.field_name, 3)
        entry.connect('key-press-event', self.keypress_event_cb,  self.field_name)
        entry.connect('key-release-event', self.keypress_event_cb,  self.field_name, 'release')

        
### Filling & popping the completion
    def show_possible_completion(self, widget, mode, pop=True):
        """
        fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """
        self.mode = mode
        # TIP: status bar 
        self.master.sb(_("search mode: %s") % mode)
        self.model.clear()

        result = self.select_values(self.field_name, mode)
        for obj in result:
            self.append_to_model(obj)

        if pop:
            self.make_completion_to_pop(self.get_entry())
        else: # doctest purpose
            for row in self.model:
                print self.model.get_value(row.iter, 1)

    def match_func(self, completion, key, iter):
        """When editing, this function limits the visible entry of the model
        """
        ## I want to have also group_by field in the completion, but only when
        ## thare's a match to be shown under that group
        ## so I need to passs twice, this is done just once each completion
        ## popup
        text = self.model.get_value(iter, self.DESCRIPTION_COL)
        prev = getattr(self, '_prev_match_value', None)
        
        if key != prev:
            self._prev_match_value = key
            self.model_set_match_col(key)

        return self.model.get_value(iter, self.MATCH_COL)

    def model_set_match_col(self, key):
        """
        set MATCH_COL to be returned by match_func in a 2 pass process:
        
        """

        miter_dict = {}

        for row in self.model:

            value = self.model.get_value(row.iter, self.VALUE_COL)
            text  = self.model.get_value(row.iter, self.DESCRIPTION_COL)
            obj   = self.model.get_value(row.iter, self.OBJ_COL)

            if text is None:
                ## it's not clear to me why there's a pass here with incomplete model
                ## all is working but ...
                continue

            if value is None:
                ## it's a group_by field
                self.model.set_value(row.iter, self.MATCH_COL, False)
                # store it's iter but set to false for the moment (will not match)
                miter_dict[text] = [row.iter, False]

            else:
                match = False
                ## start mode
                if self.mode == 'start' and re.search("^%s" %(key), text, re.IGNORECASE):
                    match = True
                elif re.search(key, text, re.IGNORECASE):  # regexp mode
                    match = True
                    
                if match and self._group_by:
                    ## switch ON the display of group by label in completion
                    try:
                        miter_dict[obj[self._group_by]][1] = True
                    except IndexError, e:
                        print "Probable missing value for %s" % text

                self.model.set_value(row.iter, self.MATCH_COL, match)


        for iter, val in miter_dict.values():
            self.model.set_value(iter, self.MATCH_COL, val)

    def append_to_model(self, obj):
        """
        How each selected record gets to the model
        """
        m_iter = self.model.append(None)
        self.model.set(m_iter,
                       self.VALUE_COL, getattr(obj, self.field_name),
#                       self.VALUE_COL, self.format % DictLike(obj),
                       self.MATCH_COL, True)

    def make_completion_to_pop(self, entry):
        """
        Create an event that will cause completion to pop
        """
        entry.grab_focus()
        #entry.select_region(0,0)
        entry.set_position(100)

        event =   gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        ## write something
        event.keyval = gtk.keysyms.period  #ord(".")
        event.window = entry.window
        entry.emit('key-press-event',event)

        ## and delete it...
        event.keyval = gtk.keysyms.BackSpace
        event.hardware_keycode = 22

        entry.emit('key-press-event',event)        
        return

### Call back
    def match_selected_cb(self, wdg, model, iter, field_name):
        """after selecting an entry store the value in self.values and set
        the entry with the correct value.
        """
        # the completion model has 1 or 4 columns (in case of FKey):
        # 0:  the real value to be put in the db
        # 1:  the value to be shown in the field
        # 2:  the value to be shown in the drop down completion menu
        # 3:  the row return by the SELECT when building the completion
        #         if more fields are present more columns get written

        value = model.get(iter, self.VALUE_COL)[0]

        if self.master.is_fkey(field_name):
            fkvalue = model.get(iter, self.DESCRIPTION_COL)[0]
        else:
            fkvalue = None
        
        self.master.set_value(field_name, value, fkvalue=fkvalue, initial=False)

        return True
        
### Sql SELECT
    def select_values(self, field_name, mode):
        """execute the SELECT DISTINCT and return values
        """

        oper = self.get_match_operator()
        filtering_value = self.get_displayed_value()
        self.autostart_last_length = len(filtering_value)

        sql = self.compose_select_statement(oper, filtering_value)
        self.sql = sql
        
        return self.master.metadata.bind.execute(sql)

    def compose_select_statement(self, oper, value):

        where = self.column.op(oper)(value)
        where = self.add_filters(where)
        sql = select(self.columns, where, from_obj=self.from_obj)

        return sql.order_by(self.column).distinct()
    
    def get_displayed_value(self, ):

        val = self.master.get_value(self.field_name, shown=True)
        assert isinstance(val, str)
        self.autostart_last_length = len(val)
        return self.add_for_LIKE(val)

    def get_match_operator(self):
        
        ## FIXME: pretty stupid at the moment...
        if self.mode == 'start':
            oper = self.MATCH_OPERATOR
        if self.mode == 'regexp':
            oper = self.MATCH_OPERATOR
        else:
            oper = self.MATCH_OPERATOR

        return oper

    def add_for_LIKE(self, value):
        """add a % simbol to get expansion if completion is attempted in LIKE mode""" 

        if self.MATCH_OPERATOR in ('LIKE', 'ILIKE'):
            if self.mode == 'start':
                if not value.startswith('%'):
                    value += '%'
                
            if self.mode == 'regexp':
                if not value.startswith('%'):
                    value = '%' + value + '%'
        return value
    
    def add_filters(self, where):
        """
        Add filters set with ``.filter``
        """
        if not self._filter:
            return where

        ## substitute values 
        kw = copy(self._filter)
        ignore = []
        for key, val in kw.iteritems():
            value =  self.parse_value(val)   # get a possible dynamic filter
            if value:
                kw[key] = value
            else:
                ## no value there in this moment
                ignore += [ key ]
        for key in ignore:
            del kw[key]
        if kw:
            return where & self.get_filtered_clause_list(**kw)
        else:
            return where

    def get_filtered_clause_list(self, **kw):
        """
        apply filter rules to this particular completion request,
        use mapper to follow possible further relations
        """
        
        clause_list, path = django2sqlalchemy(mapper=self.mapper, **kw)
        return clause_list

### Misc
    def autostart_completion(self):
        """
        Completion starts on demand or:
        1. when more that self.autostart chars have been written
        2. if text in entry has fewer chars than chars that triggered it
        """
        if self.autostart:
            text = self.master.get_value(self.field_name, shown=True)
            length = len(text)

            if (not self.autostart_last_length  and length >= self.autostart) \
                   or (length + 1 < self.autostart_last_length):
                autostart = self.autostart
                self.autostart = False
                self.show_possible_completion(self.widget.entry, 'regexp')
                self.autostart = autostart
        return True
    
    def pop_menu(self, wdg, ev, field_name, num_button):
        """pops a menu with chooices of different completion::
              - regexp
              - start
        """
        if not ev.button == num_button:
            return False

        try:
            self.w['M=popup'].destroy()
        except:
            pass

        
        self.master.widgets['M=popup'] = gtk.Menu()
        menu = self.master.widgets['M=popup']
        ## info on field
        item = gtk.MenuItem(label="info on %s" % field_name.replace('_','__'))
        item.connect('activate', self.show_field_info, field_name)
        label = _("Show all info on this field, db type & Co.")
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)
        
        ## possible values regexp
        # TIP: menu enty in menu on right click on down arro in fkey completion widget
        item = gtk.MenuItem(label=_("Show possible values: regexp  - Ctrl-Enter"))
        item.connect('activate', self.show_possible_completion, 'regexp')
        # TIP: yellow tip to menu entry in down arrow in completion widget
        label = _("Show all values in the db that match your string")
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## possible values starting
        item = gtk.MenuItem(label=_("Show possible values, starting - Shift-Enter"))
        item.connect('activate', self.show_possible_completion, 'start')
        label = _("Show all values in the database starting with your string")
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## edit table referenced as foreign key
        if self.master.is_fkey(field_name):
            item = gtk.MenuItem(label=_("Edit the referenced table in 'table' mode"))
            item.connect('activate', edit_foreign_key_table, (self.master, field_name, 'table'))
            label = _("Edit the table from which admitted values are taken in 'table' mode")
            self.master.lay_obj.tooltips.set_tip(item, label)
            menu.append(item)

        if self.master.is_fkey(field_name):
            item = gtk.MenuItem(label=_("Edit the referenced table in 'mask' mode"))
            item.connect('activate', edit_foreign_key_table, (self.master, field_name, 'mask'))
            label = _("Edit the table from which admitted values are taken in 'mask' mode")
            self.master.lay_obj.tooltips.set_tip(item, label)
            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True
    def keypress_event_cb(self, wdg, event, data=None, when='before'):
        """trigger various callback to keypress
        Set in miniwidgets or in text_editing_started_cb
        A callback connected with connect_after should set when to after
        """
        if isinstance(wdg, gtk.TreeView):
            pre = 'tree'
        else:
            #self.length_control(wdg, data)
            pre = 'entry'

        ksym = gtk.gdk.keyval_name(event.keyval)

        mods = ['key_' + pre]
        for prefix, mask in [('ctrl', gtk.gdk.CONTROL_MASK),
                             ('shift', gtk.gdk.SHIFT_MASK),
                             ('alt', gtk.gdk.MOD1_MASK),
                             ('mod2', gtk.gdk.MOD2_MASK),
                             ('mod3', gtk.gdk.MOD3_MASK),
                             ('mod4', gtk.gdk.MOD4_MASK),
                             ('mod5', gtk.gdk.MOD5_MASK),]:
            if event.state & mask:
                mods.append(prefix)

        ksym = '_'.join(mods + [ksym])
        #dbg.write('ksym', ksym, 'mods', mods)
        
        if when == 'release':
            self.autostart_completion()
#        print ksym
        if ksym in dir(self):
            return getattr(self, ksym)(wdg, event, data)
        return False

    def key_entry_F1(self, wdg, event, data):
        self.show_possible_completion(wdg, mode='regexp')
        return False
    
    def key_entry_shift_Return(self, wdg, event, data):
        self.show_possible_completion(wdg, mode='start')
        return True
        
    def key_entry_ctrl_Return(self, wdg, event, data):
        self.show_possible_completion(wdg, mode='regexp')
        return True
        
    def key_entry_Return(self, wdg, event, data):
        #
        return self.check_existance(wdg)

    def key_entry_Tab(self, wdg, event, data):
        # waiting for a complete handling of validation
        return False
        check = self.check_existance(wdg)
        #print check
        return check

    def check_existance(self, entry):
        """
        don't accept false fkey...
        """
        text = entry.get_text()
        if not text:
            return False

        if self.master.is_fkey(self.field_name) or self.master.relationship_mode == 'm2m':
            ## check if the text entered was in fact a complete and legal fkey
            ## or unique field (for m2m)
            try:
                self.get_obj_no_flush(text)

            except (NoResultFound, MultipleResultsFound), e:
                self.show_possible_completion(entry, mode='regexp')
                return True

        return False

    def get_obj_no_flush(self, value):
        """
        check if the object exists and .one(), but don't trigger .flush()
        """
        filter_cnd = {str(self.field_name) : value}
        query = self.master.session.query(table2mapper(self.table)).autoflush(False)
        return query.filter_by( **filter_cnd ).one()
        
    def show_field_info(self, wdg, field_name):
        """Pop a dialog to give info on the selected field"""
#         dialog = gtk.Dialog("info on %s" % field_name,
#                             None, gtk.DIALOG_MODAL,
#                             (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )
        info = ["%s: %s" % (f, self.master.fields[field_name][f]) 
                           for f in self.master.fields[field_name].keys() ]
#        label = gtk.Label("\n".join(info) )

        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format="\n".join(info))
        #dialog.action_area.pack_start(label, gtk.TRUE, gtk.TRUE, 0)
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def filter(self, **kwargs):
        """
        Add filters to the completion. Filters must be expressed in django-like syntax
        value can be in the form ``$field_name`` (see below)::

          t.completions.field1.filter(cod='$field2')

        would request

           1. to retrieve the value of field2 via t.get_value(field2)
           2. to add .filter(field2 = value) to the query that retrieves the possible
              completions

        Filter conditions are relative to the database "main" table: i.e. the table
        refereneced in the mapper of the table as 'local_table'.

        t.get_value() is relative to the SqlWidget in which completions is requested.
        This is relevant when related tables are present in the mask. Field value of the main mask
        can be referred to as ``$main.field_name``


          1. each token starting with ``$`` as in ``$title`` is stripped
             from the ``$`` and the remaining part is used as field_name and
             t.get_value(field_name) is used instead

          2. if the field_name part starts with ``main`` (as in ``$main.title``)
             t.get_value(field_name) is not issued in the active SqlWidget but in
             the SqlWidget pointed to by ``relationship_leader``

             This in general is the main SqlMask holding possibly different m2m
             tables. This make possible for  line in an m2m table to complete
             only values related to the referring header.
             
        """

        self._filter = kwargs  # used runtime by self.add_filters
        clause_list, path = django2sqlalchemy(mapper=self.mapper, **kwargs)
        ## let's build a suitable from_obj from this path:
        self.from_obj = path2join(path, self.mapper)
        
    def parse_value(self, value):
        """
        return value after 2 substitutions as described in .filter()

        """
        if isinstance(value, str) and  value.startswith('$'):
            value = value.replace('$','')
            
            if value.startswith('main.'):
                value = value.replace('main.','')
                value = self.master.relationship_leader.get_value(value)
            else:
                value = self.master.get_value(value)
        return value
        

    def __str__(self):
        return "<SimpleCompletion: %s>" % self.field_name
        
class FkeyCompletion(SimpleCompletion):
    VALUE_COL = 0
    DESCRIPTION_COL = 1
    MARKUP_COL = 2
    OBJ_COL = 3
    MATCH_COL = 4
    
        
    def __init__(self, master, widget, *args, **kw):
        SimpleCompletion.__init__(self, master, widget, *args, **kw)
        self.table, self.column = get_foreign_info(self.master, self.field_name, names=False)
        self.description = get_description(self.table, attr='description')
        self.attrs = get_description(self.table, attr='attrs')
        self.columns = [self.table.columns[name] for name in self.attrs]
        self.format    = get_description(self.table, attr='format')
        self.from_obj = None
        self.widget = widget

    def get_entry(self):
        return self.widget.entry

    def prepare_model(self):
        ## last col is for markup
        return gtk.ListStore(str, str, str, object, bool)
            
    def compose_select_statement(self, oper, value):

#        field_list = tables[self.table.name].attrs
#        field_list = [self.table.columns[name] for name in  self.attrs]

        order_by = [self.description]
        if self.group_by:
            order_by = [self._group_by] + order_by
            
        where = self.table.columns[self.description].op(oper)(value)
        where = self.add_filters(where)
        sql = select(self.columns, where, from_obj=self.from_obj)

        return sql.order_by(*order_by).distinct()

    

### What to show
    def lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
        try:
            return self.lookup_values[field_name][field_value]
        except Exception, e:
            descr_fields =  get_description(self.table)
            format =        tables[self.table.name].format
            fields = [self.table.columns[f_name] for f_name in descr_fields]

            sql = select(fields, self.column == field_value)
            all = self.master.metadata.bind.execute(sql).fetchall()

            if len(all) != 1:
                raise LookupValueNotReturningOneValue("%s returns %s values" % (sql, len(all)))
            else:
                value = format % all[0]
                try:
                    self.lookup_values[field_name][field_value] = value
                    return value
                except KeyError:
                    self.lookup_values[field_name] = {}
                    self.lookup_values[field_name][field_value] = value
                    return value

            self.lookup_values[field_name][field_value] = value
        return value

    def append_to_model(self, obj):
        """add to a model that has 4 cols:
             0: the value to be used as foreign key
             1: the value to be shown in the entry 
             2: data to be shown in the dropdown
             3: a dictionary of all fields in the returned row
                this can be used to set additional fields

        """

        obj_list = [getattr(obj, i) or '' for i in obj.keys()]
        fvalue = obj_list[0]
        try:
            fdescr = obj_list[1] or ''
        except IndexError, e:
            fdescr = obj_list[0]  # a fk that is a key, not an id and is the only one
        
#        fk_table, fk_key = get_foreign_info(self.master, self.field_name)
#        format_string    = tables[fk_table].format
#        description      = self.format % self.instance2dict(obj)
        Obj = DictLike(obj)
        description = self.format % Obj
        m_iter = self.get_iter(obj)
        ## FIXME: what if the pkey is composed?
        self.model.set(m_iter,
                       self.VALUE_COL,       fvalue,
                       self.DESCRIPTION_COL, description,
                       self.MARKUP_COL,      "   %s" % self.markup_clean(description),
                       self.OBJ_COL,         Obj,
                       self.MATCH_COL,       True,
                       )
    def get_iter(self, obj):
        # based on self.__prev_group_by_value
        #          self.__prev_group_by_iter

        if not self._group_by:
            return self.model.append(None)
        else:
            prev = getattr(self, '_prev_group_by_value', None)
            new_value = getattr(obj, self._group_by)

            self._prev_group_by_value = new_value
            if new_value is not None and  new_value == prev:
                return self.model.append(self._prev_group_by_iter)

            else:
                m_iter = self.model.append(None)
                self._prev_group_by_iter = None
                self.model.set(m_iter,
                               self.DESCRIPTION_COL, new_value,
                               self.MARKUP_COL,      "<b><i>%s</i></b>" % self.markup_clean(new_value),
                               self.MATCH_COL,       True
                               )
                m_iter = self.model.append(None)
            return m_iter
                    
    def markup_clean(self, text):
        text = re.sub('\&', '&amp;', text)
        text = re.sub('<', '&lt;', text)
        text = re.sub('>', '&gt;', text)
        return text
            
    def filter(self, **kwargs):
        """
        see doctring in SimpleCompletion
        """
        self._filter = kwargs
        #clause_list, path = django2sqlalchemy(table=self.table, **kwargs)
        ## let's build a suitable from_obj from this path:
        #self.from_obj = path2join(path, self.mapper)
        
    def get_obj_no_flush(self, value):
        """
        check if the object exists and .one(), but don't trigger .flush()
        """
        
        filter_cnd = {str(self.description) : value}
        query = self.master.session.query(table2mapper(self.table)).autoflush(False)
        return query.filter_by( **filter_cnd ).one()
        
#     def compose_binary_expression(self, **kwargs):
#         return compose_binary_expression(self.table, **kwargs)


    def get_filtered_clause_list(self, **kw):
        """
        apply filter rules to this particular completion request.
        Note: mapper is not available in the general situation, so we
        use table to build the clause. That means we cannot follow any
        further relationship.
        """
        
        clause_list, path = django2sqlalchemy(table=self.table, **kw)
        return clause_list

    def __str__(self):
        return "<FkeyCompletion: %s>" % self.field_name
        
class M2mCompletion(FkeyCompletion):
    VALUE_COL = 0
    DESCRIPTION_COL = 1
    MARKUP_COL = 2
    OBJ_COL = 3
    MATCH_COL = 4
    
        
    def __init__(self, *args, **kw):
        SimpleCompletion.__init__(self, *args, **kw)
        self.description = get_description(self.table, attr='description')
        self.attrs = get_description(self.table, attr='attrs')
        self.columns = [self.master.fields[field_name]['col'] for field_name in self.attrs]
        self.from_obj = None

        
    def match_selected_cb(self, wdg, model, iter, field_name):
        """after selecting an entry store the value in self.values and set
        the entry with the correct value.
        """

        value = model.get(iter, self.VALUE_COL)[0]

        if self.master.is_fkey(field_name):
            fkvalue = model.get(iter, self.DESCRIPTION_COL)[0]
        else:
            fkvalue = None
        ## when the Table is used to render a m2m field
        ## we don't want to "create" a new match, just pick an old one
        ## and use that one
            
        try:
            self.master.set_current(pk=value, substitute=True)
        except:
            pass
#             kw = {field_name: value}
#             try:
#                 print "CERCO, cerco: ", kw
#                 self.master.set_current(filter_by=kw, substitute=True)
#                 print "..."
#             except NoResultFound, e:
#                 print e
#                 msg = "No record for this specification: (%s=%s). Retry" % (field_name, value)
#             except MultipleResultsFound, e:
#                 print e
#                 msg = "Choice is not unique: (%s=%s). Retry" % (field_name, value)
#                 return False
        return True
        
    def __str__(self):
        return "<M2mCompletion: %s>" % self.field_name
        

### Functions
def debug_liststore(listore):
    j = 0
    for l in listore:
        iter = listore.get_iter_from_string(str(j))
        print listore.get(iter,0), listore.get(iter,1), listore.get(iter,3)
        j += 1

def edit_foreign_key_table(wdg, (master, field_name, mode)):
    """open a SqlMask to edit the table referenced by this ForeignKey"""
    ## FIXME  - works only with dbproxy

    from sqlkit.widgets import SqlMask, SqlTable
    
    ftable, fkey = get_foreign_info(master, field_name)
    if mode == 'mask':
        SqlMask(table=ftable, dbproxy=master.dbproxy)
    else:
        SqlTable(table=ftable, dbproxy=master.dbproxy)
    
def get_foreign_info(master, field_name, names=True):

    from sqlkit.db.minspect import get_foreign_info

    foreign_keys = master.fields[field_name]['fkey']
    return get_foreign_info(foreign_keys, names=names)






