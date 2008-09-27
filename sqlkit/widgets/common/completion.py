import re
import gtk
import dbg
import sqlkit
from sqlalchemy import text, Table
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

class SimpleCompletion(object):
    __metaclass__ = dbg.LogTheMethods
    MATCH_COL = 0
    def __init__(self, master, widget, field_name):

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
        self.master.mfields (mask wdgets): the mapping field_name -> widget
        
        """


        self.master = master
        self.lookup_values = {}
        self.MATCH_OPERATOR = OP[self.master.metadata.bind.name] or 'LIKE'
        self.widget = widget
        self.field_name = field_name
        self.completion = self.prepare_completion()

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

        completion.add_attribute(renderer, 'text', self.MATCH_COL)


        ## we match against the description field
        ## from the reference docs:
        # The match function is used by the entry completion to determine
        # if a row of the associated tree model should be in the completion list
        completion.set_match_func(self.match_func, self.MATCH_COL)
        self.liststore = self.prepare_liststore()
        completion.set_model(self.liststore)
        
        return completion

    def prepare_liststore(self):
        return gtk.ListStore(str)
    
    def add_completion(self, entry):
        """ add a completionEntry to an Entry
        """

        entry.set_completion(self.completion)
    
### Filling & popping the completion
    def match_func(self, completion, key, iter, column):
        
        model = completion.get_model()
        text = model.get_value(iter, column)
        if not text:
            text = ''
        # start
        if self.mode == 'start':
            if re.search("^%s" %(key), text, re.IGNORECASE):
                return True
            else:
                return False
        # regexp
        if re.search(key, text, re.IGNORECASE):
            return True

        return False

    def show_possible_completion(self, widget, field_name, mode):
        """fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """
        self.mode = mode
        self.liststore.clear()

        result = self.select_values(field_name, mode)

        for obj in result:
            self.append_to_model(obj)

        self.make_completion_to_pop(widget)

    def append_to_model(self, obj):
        self.liststore.append([getattr(obj, self.field_name)])

    def make_completion_to_pop(self, entry):
        """
        Create an event that will cause completion to pop
        """
        entry.grab_focus()

        event =   gtk.gdk.Event(gtk.gdk.KEY_PRESS)

        ## write something
        event.keyval = gtk.keysyms.period  #ord(".")
        event.window = entry.window
        entry.emit('key-press-event',event)

        ## and delete it...
        event.keyval = gtk.keysyms.BackSpace
        event.hardware_keycode = 22
        entry.emit('key-press-event',event)

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

### Sql SELECT
    def get_displayed_value(self, ):

        val = self.master.get_value(self.field_name, shown=True)
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

    def select_values(self, field_name, mode):
        """execute the SELECT DISTINCT and return values
        In case FKeys it behaves in a much more complicated way.
        The aim is to substitute the referenced value with the value that will
        normally be an id. 

        """

        # the text in the field with possibly '%' for like if no ~ avail
        filtering_value = self.get_displayed_value()
        
        sql, constraint_params = self.master.actions.on_completion(
            self.master.get_current_obj(), field_name)

        sql_dict = {
            'oper'                   : self.get_match_operator(),
            'field_name'             : self.field_name,
            'completion_constraint' : sql,
            }
        
        sql, filtering_field_name = self.compose_select_statement(sql_dict)

        s = text(sql, bind=self.master.metadata.bind)

        exec_dict={
            str(filtering_field_name) : filtering_value
            }
        exec_dict.update(constraint_params)
        dbg.write('exec_dict', exec_dict, sql)
        return s.execute(**exec_dict)
    
    def compose_select_statement(self, sql_dict):

        sql_dict.update({
            'referenced_table' : self.widget.field.db_spec['table_name']
            })

        if self.master.is_number(self.field_name) :
            ## pointless to regexp numbers... probably pointless to complete numbers?
            sql = """SELECT DISTINCT %(field_name)s
                  FROM %(referenced_table)s 
                  ORDER BY %(field_name)s
                  """    %    sql_dict
        else:
            sql = """
                SELECT DISTINCT %(field_name)s
                FROM %(referenced_table)s 
                WHERE %(field_name)s %(oper)s :%(field_name)s
                  %(completion_constraint)s
                ORDER BY %(field_name)s
                """ % sql_dict
        return (sql, self.field_name)
        
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
            item.connect('activate', edit_foreign_key_table, (self.master, field_name))
            label = "Edita la tabella da cui sono presi i valori permessi per questo \
            campo"
            self.master.lay_obj.tooltips.set_tip(item, label)
            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True
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
        self.show_possible_completion(wdg, field_name=data, mode='start')
        return True
        
    def key_entry_control_Return(self, wdg, event, data):
        self.show_possible_completion(wdg, field_name=data, mode='start')
        return True
        
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
    


class FkeyCompletion(SimpleCompletion):
    MATCH_COL = 2

    def prepare_liststore(self):
        return gtk.ListStore(str, str, str, object)
    
### What to show
    def lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
        try:
            return self.lookup_values[field_name][field_value]
        except:
            ftable, fname = get_foreign_info(self.master, field_name)
            descr_field, all = get_descriptor_fields(ftable, fname, self.master.metadata)
            if descr_field is None:
                return field_value
            sql = "SELECT %s FROM %s WHERE %s = :%s" % (
                descr_field,
                ftable, fname, fname)
            t = text(sql, bind=self.master.metadata.bind)

            all = t.execute(**{fname : field_value}).fetchall()
            if len(all) != 1:
                raise LookupValueNotReturningOneValue("%s returns %s values" % (sql, j))
            else:
                value = all[0][0]
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

        obj_list = self.instance2list(obj)
        obj_dict = self.instance2dict(obj)
        fvalue = obj_list[0]
        try:
            fdescr = obj_list[1] or ''
        except IndexError, e:
            fdescr = obj_list[0]  # a fk that is a key, not an id and is the only one
        
        fk_table, fk_key = get_foreign_info(self.master, self.field_name)
        descr = self.get_description_for_fkey(obj, fk_table) or fdescr
        self.liststore.append([ fvalue, fdescr, descr, obj_dict ])


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
            
    def compose_select_statement(self, sql_dict):

        ftable, fkey = get_foreign_info(self.master, self.field_name)
        description, field_list = get_descriptor_fields(ftable,  fkey, self.master.metadata)


        sql_dict.update({
            'referenced_table' : ftable,
            'field_name'       : fkey,
            'descriptor_field' : description,
            'order_by'          : field_list,
            'field_list'       : ",".join([fkey] + field_list.split(",")),
            })
        
        sql = """
             SELECT DISTINCT %(field_list)s
             FROM %(referenced_table)s 
             WHERE %(descriptor_field)s %(oper)s :%(descriptor_field)s
                  %(completion_constraint)s
             ORDER BY %(order_by)s
             """ % sql_dict

        return (sql, description)
        

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

def has_description(self, table):
    if table in tables:
        return bool(tables[table][0])
    return False

def get_description_fields(table):
    """Get description field to table 'table"""
    global tables

    if table in tables:
        return tables[table]
    return None

def get_description_field(table_name, metadata):
    """look if a description field is defined, if not use introspection
    return the description field or None

    """
    from sqlalchemy import Table
    global tables

    ## first time we meet this table  -> inspect w/ autoload
    if table_name not in tables:
        #import pdb; pdb.set_trace()
        tbl = Table(table_name, metadata, autoload=True)

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
    


def debug_liststore(listore):
    j = 0
    for l in listore:
        iter = listore.get_iter_from_string(str(j))
        print listore.get(iter,0), listore.get(iter,1), listore.get(iter,3)
        j += 1

def edit_foreign_key_table(master, wdg, field_name):
    """open a SqlMask to edit the table referenced by this ForeignKey"""
    ## FIXME
    ftable, fkey = get_foreign_info(master, field_name)
    sqlkit.SqlMask(table=ftable, dbproxy=master.dbproxy)
    
def get_foreign_info(master, field_name):

    from sqlkit.db.minspect import get_foreign_info

    foreign_keys = master.fields[field_name]['fkey']
    return get_foreign_info(foreign_keys)

def get_descriptor_fields(referenced_table, referenced_field, metadata):

    """search a possible field descriptor and add it to sql_dict

    This is called by two functions:
    lookup_value: to substitute the id with a description (mode=return)
    compose_select_statement: when proposing a list of completion values

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

    description_field, more_fields = \
                       get_description_field(referenced_table, metadata)

    if description_field:
        if more_fields:  # fields to be included to be used by formatting rules
            all_fields = "%s, %s" % (description_field, more_fields)
        else:
            all_fields = description_field
        return (description_field, all_fields)

    else:
        return (referenced_field, referenced_field)


class FkeyCompletion2(FkeyCompletion):
    pass
