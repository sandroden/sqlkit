import re
from sqlalchemy import *
import gtk
import dbg

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass

####### Completion
# EntryCompletion widgets are added on the fly triggered by F1, C-F1 or menu items
# select_values will get data from the db and fill a listore
# match_function filters using re.search from the listore to fill in the completion
#
class Completion(object):
    def __init__(self, master):
        """completion is the way we can find possible completions of text in a cell.
        In case the edited field has a Foreign Key constraint completion will follow
        the table/field to retrieve the possible values, in case we don't have an fk
        completion will suggest values already present in the db.

        A completion must be 'requested' (is only issued on demand). Normal bindings
        are F1 or right-click and will add an gtk.EntryCompletion on the fly to the
        widget that triggered the request, attach a listore, fill the liststore
        with values accordingly.

        widget.connect('button-press-event',self.completion.pop_menu,field_name, 3)
        widget.connect('key-press-event', self.completion.entry_short_cut_event,
                        field_name, 'F1')

        It requires quite a lot of objecta be already setup in the master
        (actually SqlMask or SqlTreeView?)
        self.master.fields: an InspectMapper Object
        self.master.engine
        self.master.lay_obj a Layout object (for the tooltips method)
        self.master.mapper
        self.master.values in case of an id, completion will substitute it with a
             description field, for the user benefit. te real value of the field
             will be hold there.
        self.master.mwidgets (mask wdgets): the mapping field_name -> widget
        
        """


        self.master = master
        self.tables = {}
        self.listores = {}  ## needed for entry_completion
        
    def _lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
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
        return value
    
    def add_completion(self, field_name, mode):
        """ add a completionEntry to an Entry
        return a listore to be filled

        ForeignKey: when the field to complete is a foreign key, the lookup table
        is analized to search if a descriptor field exits. In that case a
        cellRenderer is added to the completion to choe that data and that field is
        used in the field
        """

        entry = self.master.mwidgets[field_name][1]
        completion = entry.get_completion()
        if completion:
            return (completion.get_model(), completion)

        ## completion was not present
        completion = gtk.EntryCompletion()
        completion.set_property('minimum-key-length', 0)
        completion.connect('match-selected', self.match_selected_cb, field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
            
        ## FIXME: piu' generale per caso in cui si mettano anche altri campi
        if self.master.fields[field_name]['fkey']:
            col_num = 2
        else:
            col_num = 1
            
        listore = gtk.ListStore(*[str for x in range(col_num)])
            
        ## we match against the description field
        completion.set_match_func(self.match_func, (col_num-1, mode))

        self.listores[field_name] =  listore
        if mode == 'regexp':
            completion.insert_action_text(1,'start with...')
        else:
            completion.insert_action_text(2,'regexp')

        completion.set_model(listore)
        completion.set_inline_completion(True)
        entry.set_completion(completion)
        completion.set_text_column(col_num-1)
        return (listore, completion)
    def match_selected_cb(self, wdg, model, iter, field_name):
        """after selecting an entry store the value in self.values
        """
        self.master.values[field_name] = model.get(iter,0)[0]
        
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
        sql_dict['val'] = self.master.mwidgets[field_name][1].get_text()
        if mode == 'start':
            sql_dict['oper'] = 'ILIKE'
            val = '%'
        if mode == 'regexp':
            sql_dict['oper'] = '~*'
        else:
            sql_dict['oper'] = '~'
            sql_dict['val'] = "."

        sql_dict['field_name'] = field_name
            
        listore, completion = self.add_completion(field_name, mode)
        listore.clear()
        ret = self.select_values(field_name, sql_dict)
        ## sql_dict['field_name'] may be changed by select_values if fk
        #dbg.write("field_name %s" % (sql_dict['field_name']))
        #dbg.write("listore is: %s" % listore)
        for R in ret:
            #listore.append([getattr(R, sql_dict['field_name'])])
            dbg.write("R: %s" % R)
            listore.append(R)
#        completion.complete()
        event =   gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = gtk.keysyms.period  #ord(".")
        event.window = self.master.mwidgets[field_name][1].window
        self.master.mwidgets[field_name][1].emit('key-press-event',event)
        event.keyval = gtk.keysyms.BackSpace
        event.hardware_keycode = 22
        #event.window = self.mwidgets[field_name][1].window
        ## FIXME: non funziona
        self.master.mwidgets[field_name][1].emit('key-press-event',event)
        
    def select_values(self, field_name, sql_dict):
        """execute the SELECT DISTINCT and return values
        In case FKeys it behaves in a much more complicated way.
        The aim is to substitute the referenced value with the value that will
        normally be an id. It will try to do that *if* the name of the field
        terminates with _id.

        """

        I = self.master.fields[field_name]
        exec_dict={field_name : sql_dict['val']}
        ### field is a ForeignKey
        if I['fkey']:
            sql_dict['table_name'] = I['fkey'][0]
            sql_dict['field_name'] = I['fkey'][1]
            self._add_descriptor_fields(sql_dict)
            sql = """SELECT DISTINCT %(field_name)s,%(descr)s
                 FROM %(table_name)s 
                 WHERE %(descr)s %(oper)s :%(descr)s
                 ORDER BY %(descr)s
                 """ % sql_dict
            exec_dict.update({sql_dict['descr'] : sql_dict['val']})
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

        dbg.sql_debug(sql, exec_dict)
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
        SqlMask.tables[table_name] = [field_name[,field_name], [format]]

        In the future 'format' will hold format info for the completion entry

        """
        
        if not table_name:
            table_name = sql_dict['table_name']
            
        if table_name not in self.tables:
            table = Table(table_name, engine=self.master.engine, autoload=True)
            #dbg.write("type: %s" % type(table))              
            #dbg.write("ora: table %s - keys: %s" % (table, table.c.keys()))
            
            #self.tables[table_name] = table
            for field_name in table.c.keys():
                #dbg.write("cercao %s" % field_name)
                if re.search('_name|_descr', field_name, re.I):
                    self.tables[table_name] = list([field_name])
                    #dbg.write(self.tables[table_name])
                    break
#                 else:
#                     dbg.write("%s non finisce per _name|_descr" % field_name)
            
        if table_name in self.tables:
            if mode == 'add':
                #sql_dict['field_name'] += ",%s" % self.tables[table_name][0]
                sql_dict['descr'] = self.tables[table_name][0]
            else:
                return self.tables[table_name][0]
        else:
            txt = "table %s does not have a descriptor field \
            to use instead of id: %s" % (table_name, table.c.keys())
            raise MissingDescriptorField(txt)
    
    def edit_foreign_key_table(self, wdg, field):
        """opens a SqlMask to edit the table referenced by this ForeignKey"""

        tbl  = self.master.fields[field]['table_name']
        fkey = self.master.fields[field]['fkey']
        txt = "table:  %s - fkey: %s" % (tbl, fkey)
        dbg.write(txt)
    

