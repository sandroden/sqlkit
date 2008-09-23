import re
from sqlalchemy import *
import gtk
import dbg
import sqlkit

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass
class UnhandledMultipleForeignkeys(Exception): pass

####### Completion
# EntryCompletion widgets are added on the fly triggered by F1, C-F1 or menu items
# select_values will get data from the db and fill a listore
# match_function filters using re.search from the listore to fill in the completion
#
tables = {}

OP = {
    'sqlite' : 'LIKE',
    'postgres'     : '~*',
    'mysql'  : 'ILIKE',
    }

class Completion(object):
    __metaclass__ = dbg.LogTheMethods
    def __init__(self, master):

        """completion is the way we can find possible completions of text in
        a cell.  In case the edited field has a Foreign Key constraint
        completion will follow the table/field to retrieve the possible
        values, in case we don't have an fk, completion will suggest values
        already present in the db.

        A completion must be 'requested' (is only issued on demand). Normal
        bindings are F1 Control_Enter or right-click and will add a
        gtk.EntryCompletion on the fly to the widget that triggered the
        request, attach a listore, fill the liststore with values
        accordingly.

        Bindings are set in SqlText inside text_editing_started_cb
        while in SqlMask inside miniwidets (actually only VarcharWidget and FKeyWidget)

        widget.connect('button-press-event',self.completion.pop_menu,field_name, 3)
        widget.connect('key-press-event', self.completion.entry_short_cut_event,
                        field_name, 'F1')

        It requires quite a lot of object be already setup in the master
        (actually SqlMask or SqlTable?)
        self.master.fields: an InspectMapper Object
        self.master.engine
        self.master.lay_obj a Layout object (for the tooltips method)
        self.master.mapper
        self.master.values in case of an id, completion will substitute it
             with a description field, for the user benefit. The real value
             of the field will be hold there.
        self.master.mfields (mask wdgets): the mapping field_name -> widget
        
        """


        self.master = master
#        self.tables = {}
        self.listores = {}  ## needed for entry_completion
        self.lookup_values = {}
        self.LIKE_OP = OP[self.master.metadata.bind.name]

    def prepare_completion(self, field_name, mode='regexp', match_col=0):
        """
        Prepare an EntryCompletion suitable for... sqlcompletion
        """

        completion = gtk.EntryCompletion()
        completion.set_property('popup-set-width', False)
        completion.set_property('minimum-key-length', 0)
        completion.connect('match-selected', self.match_selected_cb, field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)

        completion.add_attribute(renderer, 'text', match_col)


        ## we match against the description field
        ## from the reference docs:
        # The match function is used by the entry completion to determine
        # if a row of the associated tree model should be in the completion list
        completion.set_match_func(self.match_func, (match_col, mode))
        return completion


    def add_simple_completion(self, field_name, mode, wdg = None):
        """ add a completionEntry to an Entry. No foreign key
        """

        completion = self.prepare_completion(field_name, match_col=0)
        listore = gtk.ListStore(str)
        completion.set_model(listore)
        
        wdg.set_completion(completion)
        return (listore, completion)
    
    def add_completion(self, field_name, mode, wdg = None):
        """ add a completionEntry to an Entry
        return a listore to be filled

        ForeignKey: when the field to complete is a foreign key, the lookup table
        is analized to search if a descriptor field exists. In that case a
        cellRenderer is added to the completion to show that data and that field is
        used in the field
        """

        if wdg is None:
            entry = self.master.get_widget(field_name)
        else:
            entry = wdg
            
        completion = entry.get_completion()

        ## completion was not present
        completion = gtk.EntryCompletion()
        completion.set_property('popup-set-width', False)
        completion.set_property('minimum-key-length', 0)
        completion.connect('match-selected', self.match_selected_cb, field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
            
        if self.master.is_fkey(field_name):
            col_num = 3
            col_entry = 2   # col for data to be shown *in the entry*
            col_dropdown = 2   # col for data to be shown *in the dropdown*
            completion.add_attribute(renderer, 'text', 2)
        else:
            col_num = 1
            col_entry = 0
            col_dropdown = 0
            completion.add_attribute(renderer, 'text', 0)
            
        ## object col is to hold a dict of all values
        col_def = [str for x in range(col_num)] + [object]
        listore = gtk.ListStore( *col_def)
            
        ## we match against the description field
        ## from the reference docs:
        # The match function is used by the entry completion to determine
        # if a row of the associated tree model should be in the completion list
        completion.set_match_func(self.match_func, (col_entry, mode))

        self.listores[field_name] =  listore
#         if mode == 'regexp':
#             completion.insert_action_text(1,'start with...')
#         else:
#             completion.insert_action_text(2,'regexp')

        completion.set_model(listore)
        
        #completion.set_inline_completion(True)  'Segfault'a in gtk2.6
        #completion.set_text_column(col_entry)
        
        entry.set_completion(completion)
        return (listore, completion)
    
    
    def make_completion_to_pop(self, wdg):
        """
        Create an event that will cause completion to pop
        """
        if isinstance(wdg, gtk.ComboBoxEntry):
            wdg = wdg.child

#        completion.complete()
        event =   gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = gtk.keysyms.period  #ord(".")
        event.window = wdg.window
        wdg.emit('key-press-event',event)
        event.keyval = gtk.keysyms.BackSpace
        event.hardware_keycode = 22
        #event.window = self.get_widget(field_name).window
        ## FIXME: non funziona
        wdg.emit('key-press-event',event)

        

### What to show
    def lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
        try:
            return self.lookup_values[field_name][field_value]
        except:
            #import pdb; pdb.set_trace()
            #dbg.write("%s %s" % (field_name,field_value))
            ftable, fname = self.get_foreign_info(field_name)
            #ftable, fname = self.master.fields[field_name]['fkey']
            descr_field = self._add_descriptor_fields(
                mode='return', referenced_table=ftable, referenced_field=fname)
            if descr_field is None:
                return field_value
            sql = "SELECT %s FROM %s WHERE %s = :%s" % (
                descr_field,
                ftable, fname, fname)
            t = text(sql, bind=self.master.metadata.bind)
            ret = t.execute(**{fname : field_value})
            j = 0
            for R in ret:
                value = R[0]
                j += 1
                if not j == 1:
                    raise LookupValueNotReturningOneValue("%s returns %s values" % (sql, j))
            try:
                a = value
            except:
                self.lookup_values[field_name][field_value] = field_value
                return field_value
            if not field_name in self.lookup_values:
                self.lookup_values[field_name] = {}
            self.lookup_values[field_name][field_value] = value
        return value

    def get_foreign_info(self, field_name):

        from sqlkit.db.minspect import get_foreign_info

        foreign_keys = self.master.fields[field_name]['fkey']
        return get_foreign_info(foreign_keys)

### Filling the completion
    def match_func(self, completion, key, iter, func_data):
        column, mode = func_data
        model = completion.get_model()
        text = model.get_value(iter, column)
        #dbg.write("column: %s  - mode: %s" % (column, mode))
        if not text:
            text = ''
        #return False
        # start
        if mode == 'start':
            if re.search("^%s" %(key), text, re.IGNORECASE):
                return True
            else:
                return False
        # regexp
        if re.search(key, text, re.IGNORECASE):
            #dbg.write("accetto: %s col: %s" % (text, column))
            return True
        #dbg.write("rifiuto: %s" % text)
        return False

    def show_possible_completion(self, widget, field_name, mode):
        """fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """

        # liststore = self.master.get_completion_listore(field_name, mode, widget)
        liststore = self.get_liststore(field_name, mode, widget)
        liststore.clear()

        result = self.select_values(field_name, mode)

        for obj in result:
            if self.master.is_fkey(field_name):
                self.append_to_model_fkey(liststore, obj, field_name)
            else:
                ## we're selection in the same column where we triggered completion
                liststore.append([getattr(obj, field_name)])

        dbg.write("%s - %s" % ('make_completion_to_pop', widget))
        self.make_completion_to_pop(widget)

    def append_to_model_fkey(self, liststore, obj, field_name):
        """add to a model that has 4 cols:
             0: the value to be used as foreign key
             1: the value to be shown in the entry 
             2: data to be shown in the dropdown
             3: a dictionary of all fields in the returned row
                this can be used to set additional fields

        """


        obj_list = self.instance2list(obj)
        obj_dict = self.instance2dict(obj)
        fvalue = obj_list[0]
        try:
            fdescr = obj_list[1] or ''
        except IndexError, e:
            fdescr = obj_list[0]  # a fk that is a key, not an id and is the only one
        
        #fk_table = self.master.fields[field_name]['fkey'][0]
        fk_table, fk_key = self.get_foreign_info(field_name)
        descr = self.get_description_for_fkey(obj, fk_table) or fdescr
        dbg.write(fvalue, fdescr, descr, obj_dict )
        liststore.append([ fvalue, fdescr, descr, obj_dict ])

    def get_description_for_fkey(self, obj, fk_table):
        """get the best possible description for a record. Should be
        the __str__ of that instance but we don't always have it.

        At the moment the description is the first matching of:
          - a description defined via set_description_field (if any))
          - the first string column of the table
        """
        
        if fk_table in tables and tables[fk_table][2] is not None:
            description = tables[fk_table][2] % self.instance2dict(obj)
        else:
            description = " - ".join(self.instance2list(obj)[2:])

        return description

    def get_liststore(self, field_name, mode, widget):
        """return the liststore associated with widget (that can be Entry or ComboBoxEntry)
        """
        if isinstance(widget, gtk.ComboBoxEntry):
            #return widget.childget_model()
            widget = widget.child

        return widget.get_completion().get_model()
        
#     def show_possible_completion_old(self, wdg, field_name, mode):
#         """fill in a ListStore to use with completion, fetch data from db
#         mode determines the match of the already typed text:
#         start: only matching data starting with typed text
#         regexp: typed text is a regexp (*~ or ILIKE)
#         all: all values
#         """

#         sql_dict = {}
#         sql_dict['val'] = self.master.get_value(field_name, shown=True)
            
#         if mode == 'start':
#             sql_dict['oper'] = self.LIKE_OP
#         if mode == 'regexp':
#             sql_dict['oper'] = self.LIKE_OP
#         else:
#             sql_dict['oper'] = self.LIKE_OP

#         self.add_for_LIKE(sql_dict, mode)
#         sql_dict['field_name'] = field_name
            
#         liststore, completion = self.add_completion(field_name, mode, wdg)
#         liststore.clear()
#         ret = self.select_values(field_name, sql_dict)
# #        self.add_NULL_value(liststore)
#         for R in ret:
#             Rl = self.instance2list(R)
#             dbg.write(Rl)
#             Rd = self.instance2dict(R)

#             if self.master.is_fkey(field_name):
#                 fk_table = self.master.fields[field_name]['fkey'][0]
#                 dbg.write("fk_table: %s" % fk_table)

#                 if fk_table in tables and tables[fk_table][2] is not None:
#                     # we have defined explicitly a format via "str" % dict
#                     descr = tables[fk_table][2] % Rd
#                     liststore.append([ Rl[0], Rl[1], descr, Rd ])

#                 elif len(Rl) > 1:
#                     dbg.write("> 1 -- Rl", Rl)
#                     ## default format is all fields joined
#                     liststore.append([ Rl[0], Rl[1] or '', " - ".join(Rl[1:]), Rd ])

#                 else:
#                     liststore.append([ Rl[0], Rl[0] , Rl[0], Rd ])
                    
#             else:
#                 liststore.append([Rl[0], Rd])

#         self.make_completion_to_pop(wdg)
#         dbg.write(liststore)
#     def add_NULL_value(self, liststore):
#         liststore.append([{}] + [None] * (liststore.get_n_columns()-1))

    def instance2list(self, R):
        ## NOTE: a NULL from the db gets casted to ''
        ret = [getattr(R, i) or '' for i in R.keys()]
        return ret
            
    def instance2dict(self, R):
        ret = [getattr(R, i) for i in R.keys()]
        ret = {}
        for i in R.keys():
            ret[i] = getattr(R, i)
        return ret
            
    
    def debug_listore(self, listore):
        j = 0
        for l in listore:
            iter = listore.get_iter_from_string(str(j))
            print listore.get(iter,0), listore.get(iter,1), listore.get(iter,3)
            j += 1

    def add_for_LIKE(self, value, mode):
        """add a % simbol to get expansion if completion is attempted in LIKE mode""" 

        if self.LIKE_OP in ('LIKE', 'ILIKE'):
            if mode == 'start':
                if not value.startswith('%'):
                    value += '%'
                
            if mode == 'regexp':
                if not value.startswith('%'):
                    value = '%' + value + '%'
        return value
    
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

        value = model.get(iter,0)[0]

        if self.master.is_fkey(field_name):
            fkvalue = model.get(iter,1)[0]
        else:
            fkvalue = None

        if self.master.is_primary(field_name) and self.master.relationship_mode == "m2m":
            ## when the Table is used to render a m2m field
            ## we don't want to "create" a new match, just pick an old one
            ## and use that one
            self.master.set_current(pk=value, substitute=True)
        else:
            ## normal case
            self.master.set_value(field_name, value, fkvalue=fkvalue, initial=False)

        return True
#         #dbg.write('value for ', field_name, value)

#         ## Let's show a more usefull value than the id. 
#         if self.master.is_fkey(field_name):
#             # note: model.get() returns a tuple, one value each cell on the column
#             show_value = model.get(iter,1)[0]
#             Rd = model.get(iter,3)[0]
#             dbg.write("Rd: %s" % Rd)
#             Rd[field_name] = show_value
#             dbg.write("Rd: %s" % Rd)

#             dbg.write('Rd', Rd, 'Rd type', type(Rd))
                
#             self.set_text(Rd, exclude=field_name)
#             ## reset the show value
#             ##Rd[field_name] = show_value
#         else:
#             Rd = {field_name : value }
#             self.set_text(Rd)
        

#     ## FIXME for Sandro: use virtual methods by calling master.set_value
#     ## instead of checking type of master class
#     ## see the else case.
#     ## suggested name "set_value" for this method (mcm)
#     def set_text(self, Rd, exclude=None):
#         """sets the values of field read by the select
#         """
#         if isinstance(self.master, sqlkit.SqlMask):
#             for field_name, value in Rd.iteritems():
# #                 if field_name == exclude:
# #                     dbg.write('salto: ', field_name, Rd[field_name])
# #                     continue
#                 #dbg.write(field_name, value)
#                 if field_name in self.master.mfields:
#                     dbg.write("field_name : %s value: %s Rd %s" % (
#                             field_name, value, Rd))
#                     #print "self.master.set_value(%s, %s)" % (field_name, value)
#                     self.master.set_value(field_name, value)

#                     #self.master.set_value(field_name, Rd[field_name])
#                     #setattr(self.master.current, field_name, Rd[field_name])
#         else:
#             #dbg.write(Rd)
#             for field_name, value in Rd.iteritems():
#                 if field_name == exclude:
#                     #dbg.write("self.master.editable.set_text(str(value))", value)
#                     #self.master.editable.set_text(str(value))
#                     #dbg.write("%s/%s: continue" % (field_name, value))
#                     continue
#                 if field_name in self.master.field_list:
#                     #self.master.set_fkey_value(field_name, value)
#                     self.master.set_value(field_name, value)
#         return

### Sql SELECT
    def select_values(self, field_name, mode):
        """execute the SELECT DISTINCT and return values
        In case FKeys it behaves in a much more complicated way.
        The aim is to substitute the referenced value with the value that will
        normally be an id. 

        """
        global tables

        sql_dict = {}
        sql_dict['val'] = self.master.get_value(field_name, shown=True)
            
        if mode == 'start':
            sql_dict['oper'] = self.LIKE_OP
        if mode == 'regexp':
            sql_dict['oper'] = self.LIKE_OP
        else:
            sql_dict['oper'] = self.LIKE_OP

        sql_dict['val'] = self.add_for_LIKE(sql_dict['val'], mode)
        sql_dict['field_name'] = field_name
            
        
        I = self.master.fields[field_name]
        exec_dict={str(field_name) : sql_dict['val']}

        sql, constraint_params = self.master.actions.on_completion(
            self.master.get_current_obj(), field_name)

        sql_dict['completion_constraint'] = sql
        ### field is a ForeignKey
        if I['fkey']:
            ftable, fkey = self.get_foreign_info(field_name)
            ## set the referenced table' staff
            sql_dict['referenced_table'] = ftable
            sql_dict['field_name'] = fkey

            try:
                self._add_descriptor_fields(sql_dict)
            except MissingDescriptorField:
                pass
                
            #sql_dict['field_comp'] = tables[sql_dict['referenced_table']][0]
            if tables[ftable][0] is not None:
                sql_dict['descriptor_field'] = tables[sql_dict['referenced_table']][0]
                sql_dict['order_by'] = re.sub('^,', '',sql_dict['descr'])
                ## in case is not an ID but a key *and* te only field
                if not sql_dict['order_by']:
                    sql_dict['order_by'] = sql_dict['field_name']
                
            else:
                sql_dict['descriptor_field'] = fkey
                sql_dict['order_by'] = fkey
                
            #dbg.dshow(sql_dict)
            sql = """
                 SELECT DISTINCT %(field_name)s %(descr)s
                 FROM %(referenced_table)s 
                 WHERE %(descriptor_field)s %(oper)s :%(descriptor_field)s
                     %(completion_constraint)s
                 ORDER BY %(order_by)s
                 """ % sql_dict

            exec_dict.update({str(sql_dict['descriptor_field']) : sql_dict['val']})
            exec_dict.update(constraint_params)
        else:
            sql_dict['referenced_table'] = I['table_name'] 

            if I['type'] == int:
                ## pointless to regexp numbers... probably pointless to complete numbers?
                sql = """SELECT DISTINCT %(field_name)s
                FROM %(referenced_table)s 
                ORDER BY %(field_name)s
                """ % sql_dict
            else:
                sql = """
                    SELECT DISTINCT %(field_name)s
                    FROM %(referenced_table)s 
                    WHERE %(field_name)s %(oper)s :%(field_name)s
                      %(completion_constraint)s
                    ORDER BY %(field_name)s
                    """ % sql_dict
                exec_dict.update(constraint_params)

        #dbg.write(sql, exec_dict)
        #dbg.sql_debug(sql, exec_dict)
#        s = text(sql, engine=self.mapper.engines[0])
        s = text(sql, bind=self.master.metadata.bind)
        dbg.write('exec_dict', exec_dict, sql)
        return s.execute(**exec_dict)
    
    def _add_descriptor_fields(self, sql_dict=None, mode='add',
                               referenced_table=None,
                               referenced_field=None,
                               ):

        """search a possible field descriptor and add it to sql_dict

        This is called by two functions:
        lookup_value: to substitute the id with a description (mode=return)
        select_values: when proposing a list of completion values

        mode: return. If mode='return' the value is returned and only one
              field_name is returned

              add. Dict sql_dict is added a 'descr' key. more fields can be defined
              that will be usable in the label (see: set_description_field)
              In this case 'referenced_table' is a key of sql_dict


        When displaying data for foreign keys the key that is referenced may be
        a serial or a code. A descriptor field can be shown instead. A default is
        to look for the first field terminating with _name or _descr.

          Overwriting defaults (tables dictionary)
          
        You can bypass this mechanism writing a comma separated list in
        sqlkit.completion.tables[referenced_table] = [field_name[,field_name], [format]]
        use  set_description_fields for this purpouse.

        """
        global tables

        ## args parsing
        if not referenced_table:
            referenced_table = sql_dict['referenced_table']
            
        if not referenced_field and sql_dict:
            referenced_field = sql_dict['field_name']
            
        description_field, more_fields = self.get_description_field(referenced_table)
        
        if description_field is not None:
            ## called from select_values, we also have a possible description
            ## description field may be exactly field_name if it's a key
            if mode == 'add' :
                if not description_field == referenced_field:
                    sql_dict['descr'] = "," + description_field
                else:
                    sql_dict['descr'] = ""
                if more_fields:
                    sql_dict['descr'] += "," + more_fields
            else:
                ## called from lookup_value
                return description_field 
        else:
            if mode == 'add':
                sql_dict['descr'] = ''
            else:
                return referenced_field
                
#             txt = "Table %s does not have a descriptor field." % (referenced_table)
#             txt += "You may set it with function 'set_description_field'" 
#             tables[referenced_table] = (referenced_field, '')
    
    def get_description_field(self, table_name):
        """look if a description field is defined, if not use introspection
        return the description field that can be None
        
        """
        
        global tables
        
        ## first time we meet this table  -> inspect w/ autoload
        if table_name not in tables:
            #import pdb; pdb.set_trace()
            tbl = Table(table_name, self.master.metadata, autoload=True)
            
            descr_exists = False
            for field_name in tbl.c.keys():
                if re.search('_name|_descr', field_name, re.I):
                    tables[table_name] = [field_name, None, None]
                    descr_exists = True
                    break
                tables[table_name] = [None, None, None]

            ## as a last resort use the first text field
            if tables[table_name] == [None, None, None]:
                for field_name in tbl.c.keys():
                    if re.search("string|text|char", tbl.c[field_name].type.__class__.__name__, re.I):
                        tables[table_name] = [field_name, None, None]
                        break
                
        return tables[table_name][0:2]

### Misc
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

        
        self.master.w['M=popup'] = gtk.Menu()
        menu = self.master.w['M=popup']
        ## info on field
        item = gtk.MenuItem(label="info on %s" % field_name.replace('_','__'))
        item.connect('activate', self.show_field_info, field_name)
        label = "Show all info on this field, db type and such"
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)
        
#         ## possible values
#         item = gtk.MenuItem(label="possible values")
#         item.connect('activate', self.show_possible_completion, field_name, 'all')
#         label = "Mostra tutti i valori attualmente nel db"
#         self.lay_obj.tooltips.set_tip(item,label)
#         menu.append(item)

        ## possible values regexp
        item = gtk.MenuItem(label="possible values: regexp  - F1")
        item.connect('activate', self.show_possible_completion, field_name, 'regexp')
        label = "Mostra tutti i valori attualmente nel db che 'matchino'"
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## possible values starting
        item = gtk.MenuItem(label="possible values, starting - Ctrl-F1")
        item.connect('activate', self.show_possible_completion, field_name, 'start')
        label = "Mostra tutti i valori attualmente nel db, che cominciano con..."
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## edit table referenced as foreign key
        if self.master.is_fkey(field_name):
            item = gtk.MenuItem(label="Edit fk table")
            item.connect('activate', self.edit_foreign_key_table, field_name)
            label = "Edita la tabella da cui sono presi i valori permessi per questo \
            campo"
            self.master.lay_obj.tooltips.set_tip(item, label)
            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True
    def edit_foreign_key_table(self, wdg, field_name):
        """open a SqlMask to edit the table referenced by this ForeignKey"""

        ftable, fkey = self.get_foreign_info(field_name)
        sqlkit.SqlMask(table=ftable, dbproxy=self.master.dbproxy)
    
    def keypress_event_cb(self, wdg, event, data=None):
        """impleents various callback to keypress
        Set in miniwidgets or in text_editing_started_cb
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
        
        if ksym in dir(self):
            return getattr(self, ksym)(wdg, event, data)
    
    def key_entry_F1(self, wdg, event, data):
        self.show_possible_completion(wdg, field_name=data, mode='regexp')
        return True
    
    def key_entry_shift_Return(self, wdg, event, data):
        self.show_possible_completion(wdg, field_name=data, mode='regexp')
        return True
        
    def entry_short_cut_event(self, wdg, ev, field_name, key):
        """callback of key-press-button in (string) entries"""

        accelname = gtk.accelerator_name(ev.keyval, ev.state)
        if accelname == 'F1':
            self.show_possible_completion (wdg, field_name, 'like')
        elif accelname == '<Control>F1':
            self.show_possible_completion (wdg, field_name, 'regexp')
    
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
    

### Functions
def set_description_fields(table, descr, add=None, format=None):
    """Set description field to table 'table'
    add: a comma separated  list of fields that will be added to
         the SELECT to make them available to format
         
    format: can use any field that have been put in the 'add' field. Eg.:

        format = '%(city_name)s (%(city_pv)s - %(city_country)s)'
        sk.completion.set_description_fields(
             'city', 'city_name', 'city_pv, city_country', format)

    
    """
    if not add:
        add = []
    global tables
    tables[table] = (descr, add, format)
    
def get_description_fields(table):
    """Get description field to table 'table"""
    global tables

    if table in tables:
        return tables[table]
    return None
    
