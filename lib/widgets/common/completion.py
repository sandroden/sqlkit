import re
from sqlalchemy import *
import gtk
import dbg
import sqlkit

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass

####### Completion
# EntryCompletion widgets are added on the fly triggered by F1, C-F1 or menu items
# select_values will get data from the db and fill a listore
# match_function filters using re.search from the listore to fill in the completion
#
tables = {}
class Completion(object):
    def __init__(self, master):

        """completion is the way we can find possible completions of text in
        a cell.  In case the edited field has a Foreign Key constraint
        completion will follow the table/field to retrieve the possible
        values, in case we don't have an fk completion will suggest values
        already present in the db.

        A completion must be 'requested' (is only issued on demand). Normal
        bindings are F1 or right-click and will add a gtk.EntryCompletion on
        the fly to the widget that triggered the request, attach a listore,
        fill the liststore with values accordingly.

        widget.connect('button-press-event',self.completion.pop_menu,field_name, 3)
        widget.connect('key-press-event', self.completion.entry_short_cut_event,
                        field_name, 'F1')

        It requires quite a lot of object be already setup in the master
        (actually SqlMask or SqlTreeView?)
        self.master.fields: an InspectMapper Object
        self.master.engine
        self.master.lay_obj a Layout object (for the tooltips method)
        self.master.mapper
        self.master.values in case of an id, completion will substitute it
             with a description field, for the user benefit. The real value
             of the field will be hold there.
        self.master.mwidgets (mask wdgets): the mapping field_name -> widget
        
        """


        self.master = master
#        self.tables = {}
        self.listores = {}  ## needed for entry_completion
        self.lookup_values = {}
        
    def _lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
        try:
            return self.lookup_values[field_name][field_value]
        except:
            #dbg.write("%s %s" % (field_name,field_value))
            ftable, fname = self.master.fields[field_name]['fkey']
            sql = "SELECT %s FROM %s WHERE %s = :%s" % (
                self._add_descriptor_fields(mode='return', table_name=ftable),
                ftable, fname, fname)
            t = text(sql, engine=self.master.engine)
            ret = t.execute(**{fname : field_value})
            j = 0
            for R in ret:
                value = R[0]
                j += 1
                if not j == 1:
                    raise LookupValueNotReturningOneValue("%s returns %s values" % (sql, j))
            if not field_name in self.lookup_values:
                self.lookup_values[field_name] = {}
            self.lookup_values[field_name][field_value] = value
        return value
    
    def get_widget(self, field_name):
        """return the widget to widh the entryCompletion should be attached
        """
        if self.master.__class__.__name__ == 'SqlMask':
            return self.master.mwidgets[field_name]
        
    def add_completion(self, field_name, mode, wdg = None):
        """ add a completionEntry to an Entry
        return a listore to be filled

        ForeignKey: when the field to complete is a foreign key, the lookup table
        is analized to search if a descriptor field exits. In that case a
        cellRenderer is added to the completion to show that data and that field is
        used in the field
        """

        if wdg is None:
            entry = self.get_widget(field_name)
        else:
            entry = wdg
            
        completion = entry.get_completion()
        if completion:
            return (completion.get_model(), completion)

        ## completion was not present
        completion = gtk.EntryCompletion()
        completion.set_property('minimum-key-length', 0)
        completion.connect('match-selected', self.match_selected_cb, field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
            
        if self.master.fields[field_name]['fkey']:
            col_num = 3
            col_entry = 1   # col for data to be shown *in the entry*
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
        completion.set_match_func(self.match_func, (col_entry, mode))

        self.listores[field_name] =  listore
        if mode == 'regexp':
            completion.insert_action_text(1,'start with...')
        else:
            completion.insert_action_text(2,'regexp')

        completion.set_model(listore)
        
        #completion.set_inline_completion(True)  'Segfault'a in gtk2.6
        #completion.set_text_column(col_entry)
        
        entry.set_completion(completion)
        return (listore, completion)
    
    def match_selected_cb(self, wdg, model, iter, field_name):
        """after selecting an entry store the value in self.values and adjust
        the entry with the correct value.
        """
        self.master.values[field_name] = model.get(iter,0)[0]

        # note: model.get() returns a tuple, one value each cell on the column

        if self.master.fields[field_name]['fkey']:
            show_value = model.get(iter,1)[0]
            Rd = model.get(iter,3)[0]
            show_value = model.get(iter,1)[0]
            Rd[field_name] = show_value
            dbg.write("Rd", Rd, field_name)
            ## reset the show value
            ##Rd[field_name] = show_value
        else:
            show_value = model.get(iter,0)[0]
            Rd = {field_name : show_value }

        self.set_text(Rd)

    ## FIXME for Sandro: use virtual methods by calling master.set_value
    ## instead of checking type of master class
    ## see the else case.
    ## suggested name "set_value" for this method (mcm)
    def set_text(self, Rd):
        """sets the values of field read by the select
        """
        if isinstance(self.master, sqlkit.SqlMask):
            for field_name, value in Rd.iteritems():
                dbg.write(field_name, value)
                if field_name in self.master.mwidgets:
                    #dbg.write("%s.set_text(%s)" % (field_name, value))
                    self.master.mwidgets[field_name].set_text(value)
                    #self.master._set_value(field_name, Rd[field_name]
        else:
            #dbg.write(Rd)
            for field_name, value in Rd.iteritems():
                #dbg.write(field_name, value)
                self.master.set_value(field_name, value)
        return

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
    
    def entry_short_cut_event(self, wdg, ev, field_name, key):
        """callback of key-press-button in (string) entries"""

        accelname = gtk.accelerator_name(ev.keyval, ev.state)
        if accelname == 'F1':
            self.show_possible_values (wdg, field_name, 'regexp')
        elif accelname == '<Control>F1':
            self.show_possible_values (wdg, field_name, 'start')
    
    def show_possible_values(self, wdg, field_name, mode):
        """fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """
        #print "show_possible_values %s" % field_name
        sql_dict = {}
        #wdg = self.get_widget(field_name)
        sql_dict['val'] = wdg.get_text()
        #sql_dict['val'] = self.get_widget(field_name).get_text()
            
        if mode == 'start':
            sql_dict['oper'] = 'ILIKE'
            val = '%'
        if mode == 'regexp':
            sql_dict['oper'] = '~*'
        else:
            sql_dict['oper'] = '~'
            sql_dict['val'] = "."

        sql_dict['field_name'] = field_name
            
        listore, completion = self.add_completion(field_name, mode, wdg)
        listore.clear()
        ret = self.select_values(field_name, sql_dict)
        for R in ret:
            Rl = self.instance2list(R)
            Rd = self.instance2dict(R)
            if self.master.fields[field_name]['fkey']:
                ftable = self.master.fields[field_name]['fkey'][0]
                if ftable in tables and tables[ftable][2]:
                    # we have defined explicitly a format via "str" % dict
                    descr = tables[ftable][2] % Rd
                    listore.append([ Rl[0], Rl[1], descr, Rd ])
                else:
                    ## default format is all fields joined
                    listore.append([ Rl[0], Rl[1], " - ".join(Rl[1:]), Rd ])
            else:
                listore.append([Rl[0], Rd])
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
        
    def debug_listore(self, listore):
        j = 0
        for l in listore:
            iter = listore.get_iter_from_string(str(j))
            print iter
            print listore.get(iter,0), listore.get(iter,1), listore.get(iter,3)
            j += 1

    def instance2list(self, R):
        ret = [getattr(R, i) for i in R.keys()]
        return ret
            
    def instance2dict(self, R):
        ret = [getattr(R, i) for i in R.keys()]
        ret = {}
        for i in R.keys():
            ret[i] = getattr(R, i)
        return ret
            
    
    def select_values(self, field_name, sql_dict):
        """execute the SELECT DISTINCT and return values
        In case FKeys it behaves in a much more complicated way.
        The aim is to substitute the referenced value with the value that will
        normally be an id. It will try to do that *if* the name of the field
        terminates with _id.

        """
        global tables
        I = self.master.fields[field_name]
        exec_dict={field_name : sql_dict['val']}
        ### field is a ForeignKey
        if I['fkey']:
            sql_dict['table_name'] = I['fkey'][0]
            sql_dict['field_name'] = I['fkey'][1]
            self._add_descriptor_fields(sql_dict)
            sql_dict['field_comp'] = tables[sql_dict['table_name']][0]
            #dbg.dshow(sql_dict)
            sql = """SELECT DISTINCT %(field_name)s,%(descr)s
                 FROM %(table_name)s 
                 WHERE %(field_comp)s %(oper)s :%(field_comp)s
                 ORDER BY %(descr)s
                 """ % sql_dict
            #dbg.write(sql)
            exec_dict.update({sql_dict['field_comp'] : sql_dict['val']})
        else:
            sql_dict['table_name'] = I['table_name']

            if I['type'] == int:
                ## pointless to regexp numbers...
                sql = """SELECT DISTINCT %(field_name)s
                FROM %(table_name)s 
                ORDER BY %(field_name)s
                """ % sql_dict
            else:
                sql = """SELECT DISTINCT %(field_name)s
                    FROM %(table_name)s 
                    WHERE %(field_name)s %(oper)s :%(field_name)s
                    ORDER BY %(field_name)s
                    """ % sql_dict

        #dbg.sql_debug(sql, exec_dict)
#        s = text(sql, engine=self.mapper.engines[0])
        s = text(sql, engine=self.master.mapper.table.engine)
        return s.execute(**exec_dict)
    def pop_menu(self, wdg, ev, field_name, num_button):
        #print "pop_menu", wdg, ev
        if not ev.button == num_button:
            return False

        try:
            self.w['M=popup'].destroy()
        except:
            pass

        
        self.w['M=popup'] = gtk.Menu()
        menu = self.w['M=popup']
        ## info on field
        item = gtk.MenuItem(label="info on %s" % field_name.replace('_','__'))
        item.connect('activate', self.show_field_info, field_name)
        label = "Show all info on this field, db type and such"
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)
        
#         ## possible values
#         item = gtk.MenuItem(label="possible values")
#         item.connect('activate', self.show_possible_values, field_name, 'all')
#         label = "Mostra tutti i valori attualmente nel db"
#         self.lay_obj.tooltips.set_tip(item,label)
#         menu.append(item)

        ## possible values regexp
        item = gtk.MenuItem(label="possible values: regexp  - F1")
        item.connect('activate', self.show_possible_values, field_name, 'regexp')
        label = "Mostra tutti i valori attualmente nel db che 'matchino'"
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## possible values starting
        item = gtk.MenuItem(label="possible values, starting - Ctrl-F1")
        item.connect('activate', self.show_possible_values, field_name, 'start')
        label = "Mostra tutti i valori attualmente nel db, che cominciano con..."
        self.master.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## edit table referenced as foreign key
        item = gtk.MenuItem(label="Edit fk table")
        item.connect('activate', self.edit_foreign_key_table, field_name)
        label = "Edita la tabella da cui sono presi i valori permessi per questo \
        campo"
        self.master.lay_obj.tooltips.set_tip(item, label)
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True
    def _add_descriptor_fields(self, sql_dict=None, mode='add', table_name=None):
        """search a possible field descriptor and add it to sql_dict

        When displaying data for foreign keys the key that is referenced may be
        a serial or a code. A descriptor field can be shown instead. A default is
        to look for the first field terminating with _name or _descr.

        You can bypass this mechanism writing a comma separated list in
        sqlkit.completion.tables[table_name] = [field_name[,field_name], [format]]
        use  set_dSqlMaskescription_fields for this purpouse.

        In the future 'format' will hold format info for the completion entry

        """
        global tables
        if not table_name:
            table_name = sql_dict['table_name']
            
        if table_name not in tables:
            table = Table(table_name, engine=self.master.engine, autoload=True)
            for field_name in table.c.keys():
                if re.search('_name|_descr', field_name, re.I):
                    tables[table_name] = [field_name, None, None]
                    break

        if table_name in tables:
            if mode == 'add':
                sql_dict['descr'] = tables[table_name][0]
                if tables[table_name][1]:
                    sql_dict['descr'] += "," + tables[table_name][1]
            else:
                return tables[table_name][0]
        else:
            txt = "table %s does not have a descriptor field \
            to use instead of id: %s" % (table_name, table.c.keys())
            raise MissingDescriptorField(txt)
    
    def edit_foreign_key_table(self, wdg, field):
        """open a SqlMask to edit the table referenced by this ForeignKey"""

        tbl  = self.master.fields[field]['table_name']
        fkey = self.master.fields[field]['fkey']
        txt = "table:  %s - fkey: %s" % (tbl, fkey)
        #dbg.write(txt)
    

def set_description_fields(table, descr, add=None, format=None):
    """Set description field to table 'table"""
    if not add:
        add = []
    global tables
    tables[table] = (descr, add, format)
    

def get_description_fields(table):
    """Set description field to table 'table"""
    global tables
    #dbg.dshow(tables)
    return tables[table]
    

