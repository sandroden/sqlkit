import gtk
import gobject, pango
import layout
import dbg
import re, os
import inspect
import tokenize
import keyword

class wshow(object):
    
    def __init__(self, widget, lvl=0, mode='print', model=None, parent=None):
        self.mode = mode
        self.parent = parent
        self.model = model
        self.lvl = lvl
        if not widget:
            dbg.write("Manca widget")
            return
        if isinstance(widget, dict):
            widget = widget['Window']
        if model:
            if lvl == 0:
                self.parent = model.append(None)
            self.add_to_model(widget, iter=self.parent)
            
        self.scan(widget)

    def printa(self, widget, iter=None, parent=None):
        if self.mode == 'print':
            print "%s%s %s %s" % (" "*self.lvl*3,
                                  widget.name, widget.__class__, widget)
            return 
        elif self.model:
            return self.add_to_model(widget, iter=iter, parent=parent)

    def add_to_model(self, widget, iter=None, parent=None):
        #dbg.write('iter: %s, parent: %s' % (iter, parent))
        if iter:
            new = iter
        else:
            new = self.model.append(parent)
        #dbg.write('self.model.set(new, %s, %s)' % (self.lvl, widget.name))
        try:
            text = "(%s)" % widget.get_text()
        except:
            text = ''
            
        self.model.set(new,
                       0, "%s %s" % (widget.name or '', text),
                       #0, "%s %s " % (widget.name, text),
                       1, self.get_class_str(widget),
                       2, self.get_class_img(widget),
                       3, widget
                       ) 
        return new
            
    def get_class_str(self, obj):
        c = str(obj.__class__)
        m = re.search('gtk.([A-Z][A-Za-z]+)',c)
        if m:
            return m.group(1)
        else:
            m = re.search('dateedit.([A-Z][A-Za-z]+)',c)            
            if m:
                return m.group(1)
            else:
                dbg.write("Fallisce re.search per ", c)

    def get_class_img(self, obj):
        c = str(obj.__class__)
        pat = '(?:gtk|dateedit).([A-Z][A-Za-z]+)'
        re_result = re.search(pat,c)
        if re_result:
            name = re_result.group(1)
        else:
            # If it isn't a gtk or dateedit object, take all the class name
            name = c
        pix_name = "/usr/share/gazpacho/resources/base/%s.png" % (name.lower())
        if not os.path.exists(pix_name):
            return
        pixbuf = gtk.gdk.pixbuf_new_from_file(pix_name)
        return  pixbuf

    


    def scan(self, widget):

        d = {}

        children = []
        try:
            children = widget.get_children()
            #dbg.write(self.lvl, children)
        except:
            pass
        for sun in children:
            new = self.printa(sun, parent=self.parent)
            ogg = wshow(sun, lvl=self.lvl+1, mode=self.mode, model=self.model,
                        parent=new)
            d[sun] = ogg

        self.d = d

class show_widgets(object):
    """ pops a TreeView to show widget hierarchy"""

    def __init__(self, widget=None, lay=True):
        """show tree hierarchy of widgets and allows for manipulating it
           create a toplevel window or uses tv if tv= parameter is provided
           Lay = Fase prevents creating a widget. Used when other programs provide
           the widget.
        """
        self.l, self.w = self._get_layout(lay)

        if widget:
            self.add_tab_and_tree('', widget)

    def _get_layout(self, lay):

        if not lay:
            return (False, False)
        
        lay = """
        {B m=file } {O tb=gtk-quit }
          {N 
           } -
        """
        self.l = layout.Layout(lay, opts="s", title='Widget Tree')
        self.w = self.l.show()
        self.w['Window'].set_size_request(300, 500)
        self.notebook = self.w['N.0']
        self.page_number = 1
        
        self.l.connect(('tb=gtk-quit', 'clicked',
                        lambda l: self.w['Window'].destroy()))

        # key accelerators
        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_group(ord('q'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.delete)
        self.w['Window'].add_accel_group(self.accel_group)

        # menu
        #self.l.menu('m=file', ('Toplevels', lambda f: self.delete()))
        menu_item = gtk.MenuItem("toplevels")
        # dbg.dshow(self.w)
        self.w['M=file'].append(menu_item)

        sub_menu = gtk.Menu()
        menu_item.set_submenu(sub_menu)
        for w in gtk.window_list_toplevels():
            lbl = w.title
            if not lbl:
                lbl = str(w)
            m = gtk.MenuItem(lbl)
            sub_menu.append(m)
            m.connect('activate', self.add_tab_and_tree, w)
        
        self.w['M=file'].show_all()
        return self.l, self.w

    def create_model(self, tv):
        model = gtk.TreeStore(str, str, gtk.gdk.Pixbuf, gobject.TYPE_OBJECT)
        tv.set_enable_search(True)
        tv.set_search_column(0)
        tv.set_model(model)

        tvc1 = gtk.TreeViewColumn('Name')
        tvc2 = gtk.TreeViewColumn('Class')
        cell_text1 = gtk.CellRendererText()
        cell_text2 = gtk.CellRendererText()
        cell_pix1  = gtk.CellRendererPixbuf()

        tvc1.pack_start(cell_pix1, False)
        tvc1.pack_start(cell_text1, True)
        tvc2.pack_start(cell_text2, True)

        tvc1.set_attributes(cell_pix1, pixbuf=2)
        tvc1.set_attributes(cell_text1, text=0)
        tvc2.set_attributes(cell_text2, text=1)

        tv.connect('button-press-event', self.button_press_cb)

        tv.append_column(tvc1)
        tv.append_column(tvc2)
        return model

    def add_tab_and_tree(self, menu_item, toplevel):
        #dbg.write(toplevel)
        lbl = toplevel.title
        if not lbl:
            lbl = str(toplevel)
            
        tv = self.add_new_book(toplevel, lbl)
        model = self.create_model(tv)
        self.fill_model(toplevel, model)
        tv.expand_all()
        return True
    
    def add_new_book(self, widget, lbl):
        self.page_number += 1
        tv = gtk.TreeView()
        scrolled = gtk.ScrolledWindow()
        scrolled.add(tv)
        
        eventBox = self.create_custom_tab(lbl, scrolled)
        self.notebook.append_page(scrolled, eventBox)
        
        # Set the new page
        pages = gtk.Notebook.get_n_pages(self.notebook)
        self.notebook.set_current_page(pages - 1)
        self.notebook.show_all()
        return tv

    def create_custom_tab(self, text, child):
        #create a custom tab for notebook containing a
        #label and a button with STOCK_ICON
        eventBox = gtk.EventBox()
        tabBox = gtk.HBox(False, 2)
        tabLabel = gtk.Label(text)

        tabButton=gtk.Button()
        tabButton.connect('clicked', self.remove_book, child)

        #Add a picture on a button
        self.add_icon_to_button(tabButton)
        iconBox = gtk.HBox(False, 0)

        eventBox.show()
        tabButton.show()
        tabLabel.show()

        tabBox.pack_start(tabLabel, False)
        tabBox.pack_start(tabButton, False)

        # needed, otherwise even calling show_all on the notebook won't
        # make the hbox contents appear.
        tabBox.show_all()
        eventBox.add(tabBox)
        return eventBox

    def add_icon_to_button(self, button):
        iconBox = gtk.HBox(False, 0)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        gtk.Button.set_relief(button, gtk.RELIEF_NONE)
        #gtk.Button.set_focus_on_click(button,False)
        settings = gtk.Widget.get_settings (button)
        (w,h) = gtk.icon_size_lookup_for_settings (settings, gtk.ICON_SIZE_MENU)
        gtk.Widget.set_size_request (button, w + 4, h + 4)
        image.show()
        iconBox.pack_start(image, True, False, 0)
        button.add(iconBox)
        iconBox.show()
        return


    # Remove a page from the notebook
    def remove_book(self, button, child):
        page = self.notebook.page_num(child)
        if page != -1:
            self.notebook.remove_page(page)
        # Need to refresh the widget --
        # This forces the widget to redraw itself.
        self.notebook.queue_draw_area(0, 0, -1, -1)


    def remove_current_book(self, *arguments, **keywords):
        page = self.notebook.get_current_page()
        if page != -1:
            self.notebook.remove_page(page)
        return True

    # Remove a page from the notebook
  
    
    def delete(self,*args):
        #dbg.write()
        self.w['Window'].destroy()
        return True
    
    def pop_menu(self, widget, ev):
        try:
            self.w['M=popup'].destroy()
        except:
            pass

        
        self.w['M=popup'] = gtk.Menu()
        menu = self.w['M=popup']

        ## info on properties
        item = gtk.MenuItem(label="properties")
        item.connect('activate', self.show_widget_properties, widget )
        menu.append(item)

        ## info on pack
        item = gtk.MenuItem(label="packing")
        item.connect('activate', self.show_widget_packing, widget )
        menu.append(item)

        ## info on properties
        item = gtk.MenuItem(label="signal")
        item.connect('activate', self.show_widget_signal, widget )
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)

    def show_widget_properties(self, menu, widget ):
        props = gobject.list_properties(widget)
        cols = ['name','value','owner_type', 'value_type','nick' ]
        a = TreeInfoLayout(cols)
        cell = a.tvc[1].get_cell_renderers()[0]
        cell.set_property('editable', True)
        #tv.set_property('resizable', True)
        cell.connect('edited', self.edited_cb, (widget, a.model, 1))
        a.w['Window'].set_title("%s - %s" % (
            widget.name or '',
            re.search("'(.*)'",str(widget.__class__)).group(1)
            )
                                )
        m = a.model
        for i in props:
            #dbg.write(i)
            iter = m.append(None)
            m.set(iter,
                  0, i.name,
                  4, i.nick,
                  2, re.search(' ([a-zA-Z]+)', str(i.owner_type)).group(1), 
                  3, re.search(' ([a-zA-Z]+)', str(i.value_type)).group(1),
                 )
            try:
                default = i.default_value
            except:
                default = ''
            #dbg.write('widget.get_property(i.name)', i.name)
            try:
                ## eg: pattern is write only, so no get_property()...
                val = widget.get_property(i.name)
            except:
                None
            if val != default and default != '':
                val = "%s (%s)" % (val, default)
                
            if i.name not in 'user-data':
                m.set(iter,
                      1, val,
                      )

        iter = m.append(None)
        m.set(iter,
              0, 'self',
              1, widget)

    def show_widget_signal(self, menu, widget, model=None ):
        dbg.write("widget", widget, widget.__class__)
        if not model:
            cols = ['name']
            a = TreeInfoLayout(cols)
            a.tv.expand_all()
            model = a.model
            
        props = gobject.signal_list_names(widget)
        iter = model.append(None)
        pat = '(?:<gtk.| )([a-zA-Z]+)'
        model.set(iter,
                  0, re.search(pat, str(widget)).group(1),
                  )

        for i in props:
            new = model.append(iter)
            model.set(new, 
                  0, i
                  )
        try:
            widget =  gobject.type_parent(widget)
            self.show_widget_signal('', widget, model=model )
        except RuntimeError:
            pass
        

    def edited_cb(self, cell, path, new_text, user_data):

        widget, model, column = user_data
        model[path][column] = new_text
        prop   = model[path][0]
        gtype  = model[path][3]

        #dbg.write('widget.set_property(%s, %s)' % (new_text,prop)   )
        py_type = {
            'gboolean' : bool,
            'gint'     : int,
            'guint'     : int,
            'gchararray' : str,
            'gfloat'   : float,
            }
        widget.set_property(prop, py_type[gtype](new_text))
        
        return
    
    def show_widget_packing(self, menu, widget):
        parent = widget.get_parent()
        # This was the first version:
#       if not gobject.type_is_a(parent, gtk.Container):
        # I now think it's OK to assume that every "parent" widget is Container:
        if not parent:
            dialog, l = self.l.message(type='warning',
                                       text="Only widgets inside a gtkContainer have packing properties.")
            self.response = dialog.run()
            dialog.destroy()
            return dialog

        props = parent.list_child_properties()
        cols = ['name','value','owner_type', 'value_type','nick' ]
        a = TreeInfoLayout(cols)
        cell = a.tvc[1].get_cell_renderers()[0]
        cell.set_property('editable', True)
        cell.connect('edited', self.edited_cb_packing, (parent, widget, a.model, 1))

        a.w['Window'].set_title("%s - %s" % (
            widget.name or '',
            re.search("'(.*)'",str(widget.__class__)).group(1)
            )
                                )
        m = a.model

        for prop in props:
            iter = m.append(None)
            m.set(iter,
                  0, prop.name,
                  4, prop.nick,
                  2, re.search(' ([a-zA-Z]+)', str(prop.owner_type)).group(1), 
                  3, re.search(' ([a-zA-Z]+)', str(prop.value_type)).group(1),
                 )
            try:
                default = prop.default_value
            except:
                default = ''
            val = parent.child_get_property(widget, prop.name)
            try:
                ## in the eventuality of write only properties
                val = parent.get_child_property(prop.name)
            except:
                None
            if val != default and default != '':
                val = "%s (%s)" % (val, default)
                
            if prop.name not in 'user-data':
                m.set(iter,
                      1, val,
                      )


    def edited_cb_packing(self, cell, path, new_text, user_data):
        parent, widget, model, column = user_data
        prop   = model[path][0]
        gtype  = model[path][3]

        py_type = {
            # Ugly way to require a number smaller than 8.
            'GtkAttachOptions' : (lambda x : int(x) if int(x) in range(8) else int('')),
            'gint'     : int,
            'guint'     : int,
            'gchararray' : str,
            'gfloat'   : float,
            }
        try:
            value = py_type[gtype](new_text)
        except:
            # The text can not be interpreted as the given type!
            value = self.edited_fallback_dialog(gtype, widget, prop, parent.child_get_property(widget, prop))

        # Now the value is valid.
        parent.child_set_property(widget, prop, value)
            
        # Whatever happened, just show (nicely) the actual value:
        model[path][column] = str(parent.child_get_property(widget, prop))
        return
        
    def edited_fallback_dialog(self, gtype, widget, prop_name, current_value):
        """If the value for a particular property is not valid, this method is
        called to get an appropriate value. It can be tought how to act with
        different gtypes by adding "elif" tests.
        """
        if gtype == 'GtkAttachOptions':
            dialog = gtk.Dialog(title=prop_name, flags=gtk.DIALOG_MODAL, buttons =('gtk-close',4))
            dialog.set_size_request(200,-1)
            checkbuttons = [gtk.CheckButton('Expand'), gtk.CheckButton('Shrink'), gtk.CheckButton('Fill')]
            for index in range(3):
                dialog.vbox.pack_start(checkbuttons[index])
                single_value = bool(int(current_value) & 2**index)
                checkbuttons[index].set_active(single_value)
                checkbuttons[index].show()
            response = dialog.run()
            value = 0
            for index in range(3):
                if checkbuttons[index].get_active():
                    value += 2**index
            dialog.destroy()
            return value
        # If we don't know kow to treat the gtype, just stick to current value
        return current_value

        
    def show_widget_connect(self):
        pass
    
    def button_press_cb(self, wdg, ev):
        if ev.button == 3:
            model = wdg.get_model()
            iter = model.get_iter(wdg.get_path_at_pos(int(ev.x), int(ev.y))[0])
            widget = model.get_value(iter,3)
            #dbg.write("Type: %s" % type(widget))
            self.pop_menu(widget, ev)
    
    def fill_model(self, toplevel, model):

        model.clear()
        i = wshow(toplevel, mode='', model=model)

class TreeInfoLayout(object):
    def __init__(self, cols, tv=None, model=None):
        if tv:
            self.tv = tv
        else:
            self.l = self._get_layout()
            self.w = self.l.show()
            self.tv = self.w['TV=a']
            self.l.connect(('tb=gtk-quit', 'clicked',
                            lambda l: self.w['Window'].destroy()))

        if not model:
            self.model = gtk.TreeStore(*[str for i in cols])
        else:
            self.model = model
        self.tv.set_enable_search(True)
        self.tv.set_model(self.model)

        self.tvc = {}
        for i,col in enumerate(cols):
            self.tvc[i] = gtk.TreeViewColumn(col, gtk.CellRendererText(), text=i)
            self.tvc[i].set_sort_column_id(i)
            self.tv.append_column(self.tvc[i])


    def _get_layout(self):
        lay = """
          {O tb=gtk-quit}
          TVS=a
        """
        #dbg.write()
        return layout.Layout(lay, opts="s")
    
SimpleTreeView = TreeInfoLayout

class ShowMapperInfo(object):
    def __init__(self, InspectMapper):
        self.info = InspectMapper
        cols = ['name', 'col__spec', 'pkey', 'fkey', 'Null', 'edit', 'table', ]
        self.treeLayout = TreeInfoLayout(cols)
        self.tv = self.treeLayout.tv
        self.model = self.treeLayout.model
        self.fill_model()
        self.tv.expand_all()

    def fill_model(self):
        iter = {}
        for table_name in self.info.tables():
            iter[table_name] = self.model.append(None)
            self.model.set(iter[table_name],  0, table_name)

            for f in self.info.table_fields(table_name):
                I = getattr(self.info, f)
                sun = self.model.append(iter[I['table_name']])
                self.model.set(sun,
                          0, I['name'],
                          1, I['col_spec'],
                          5, I['edit'],
                               )
                if I['pkey']:
                    self.model.set(sun,
                          2, I['pkey'],
                                   )
                if I['fkey']:
                    self.model.set(sun,
                          3, "%s.%s" % (I['fkey'][0], I['fkey'][1]),
                                   )
                    
                if not I['nullable']:
                    self.model.set(sun,
                          4, 'NOT NULL',

                          )
                self.model.set(sun, 6, I['table'])
        
class ShowClassInfo(object):
    def __init__(self, obj):
        cols = ['what', 'value', 'type' ]
        self.colors = {
            'dict' : 'red',
            'list' : 'blue',
            'int'  : 'seagreen',
            'NoneType'  : 'gray60',
            'tuple': 'darkslategray',
            }
        self.exclude = [
            "wrapper_descriptor",
#            "module",
            "method_descriptor",
            "member_descriptor",
#            "instancemethod",
            "builtin_function_or_method",
            "frame",
            "classmethod",
            "classmethod_descriptor",
            "_Environ",
#            "MemoryError",
            "_Printer",
            "_Helper",
            "getset_descriptor",
            "weakref",
            "cell",
            "staticmethod"            
            ]
        self.model = gtk.TreeStore(str, str, str, object, str)
        self.treeLayout = TreeInfoLayout(cols, model=self.model)
        self.tv = self.treeLayout.tv
        #self.tv.set_property('fixed-height-mode', True)
        self.tv.set_enable_search(True)
        self.tv.set_search_column(4)
        self.treeselection = self.tv.get_selection()
        #self.model = self.treeLayout.model
        self.add_to_model(obj)
        self.tv.expand_all()

        key_col = self.tv.get_column(0)
        cell = key_col.get_cell_renderers()[0]
        key_col.set_attributes(cell, markup=0)
        
        type_col = self.tv.get_column(2)
        cell = type_col.get_cell_renderers()[0]
        cell.set_property('style', pango.STYLE_ITALIC)
        type_col.set_attributes(cell, markup=2)
        

        value_col = self.tv.get_column(1)
        value_col.set_max_width(200)
        value_col.set_expand(True)
        for i in range(2):
            col = self.tv.get_column(i)
            col.set_resizable(True)
        
        self.tv.connect('button-press-event', self.add_to_model_cb)
        self.treeselection.connect('changed', self.selection_changed_cb)

    def selection_changed_cb(self, ts):
        model, iter = ts.get_selected()
        if not iter:
            return
        value = model.get_value(iter,4)
        if not value:
            return
        txt = []
        txt.insert(0, value)
        while True:
            iter=model.iter_parent(iter)
            if not iter:
                break
            path = self.model.get_path(iter)
            value = model.get_value(iter,4)
            if value:
                txt.insert(0,value)
            
        msg = ".".join(txt)
        self.treeLayout.l.sb(msg)
        
    def add_to_model(self, obj, position=None):
        iter = {}
        if obj == '':
            for key in dir():
                it = self.model.append(position)
                self.model.set(it,
                               0, key,
                               1, eval(key), 
                               )

        class_name = obj.__class__.__name__
        if class_name in ('NoneType','str', 'bool', 'type','datetime.date', 
                          'datetime.datetime', 'datetime.time','int'):
            ## it reset the value but not trimmed to 100 chars
            self.model.set(position,
                           1, str(obj))
            return
        if position is not None and self.model.iter_has_child(position):
            return

        if class_name in ('dict'):
            for key, val in obj.iteritems():
                it = self.model.append(position)
                self.add_row(it, val, str(key), val.__class__.__name__, type(val))

        elif class_name in ('list','tuple'):
            for pos,val in enumerate(obj):
                it = self.model.append(position)
                self.add_row(it, val, pos, val.__class__.__name__, type(val))

        elif inspect.ismethod(obj):
            self.info_method(obj)
        else:
            for i in ['module','callable', 'globals', 'attribute']:
                iter[i] = self.model.append(position)
                self.model.set(iter[i],
                               0, i,
                               )
            iter['builtin'] = self.model.append(iter['callable'])
            self.model.set(iter['builtin'],
                           0,'builtin')

            iter['methods'] = self.model.append(iter['callable'])
            self.model.set(iter['methods'],
                           0,'methods')

            for j in dir(obj):
                self.show_obj(obj, j, iter)
                
        for k in ['builtin', 'methods'] + iter.keys():
            try:
                if not self.model.iter_has_child(iter[k]):
                    self.model.remove(iter[k])
            except:
                pass
            
    def show_obj(self, obj, attr_name, iter):

        attr = getattr(obj, attr_name, None)
        class_name = attr.__class__.__name__

        t = type(getattr(obj, attr_name))

        if class_name == 'module':
            it = self.model.append(iter['module'])

        elif class_name in ['instancemethod', 'method-wrapper']:
            it = self.model.append(iter['methods'])
            #dbg.write(attr_name, class_name, self.model.get_path(it))
            
        elif class_name in self.exclude:
            it = self.model.append(iter['builtin'])
            #dbg.write(attr_name, class_name, self.model.get_path(it))

        elif callable(attr):
            it = self.model.append(iter['callable'])

        else:
            it = self.model.append(iter['attribute'])
            #dbg.write(attr_name, class_name, self.model.get_path(it))


        self.add_row( it, attr, attr_name, class_name, t)

    
    def add_row(self, iter, attr, attr_name, class_name, t):
        fmt = "<span foreground='maroon'>%s</span>"
        self.model.set(iter,
                       0, self.add_color(attr_name, class_name, attr),
                       1, str(attr)[0:100],  # str TreeColumn
                       2, fmt % t.__name__,
                       3, attr,  # object TreeColumn
                       4, attr_name,
                       )  
        
    def add_color(self, attr_name, class_name, attr):
        fmt = "<span foreground='%(col)s'>%(attr_name)s</span>"
        fmt_dict = {
            'col' : self.colors.setdefault(class_name,'slategray'),
            'attr_name' : re.sub('[<>]', '', str(attr_name))
            }
        return fmt % fmt_dict

    
    def add_to_model_cb(self, wdg, ev):
        if ev.button != 3:
            return False
        iter = self.model.get_iter(
            wdg.get_path_at_pos(int(ev.x), int(ev.y))[0])
        obj = self.model.get_value(iter,3)
        self.add_to_model(obj, position=iter)

        path = self.model.get_path(iter)
        self.tv.expand_to_path(path)


    def info_method(self, obj):
        """show info on method 'obj' using text widget"""
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
        

class InputStream(object):
    """ Simple Wrapper for File-like objects. [c]StringIO doesn't provide
        a readline function for use with generate_tokens.
        Using a iterator-like interface doesn't succeed, because the readline
        function isn't used in such a context. (see <python-lib>/tokenize.py)
    """
    def __init__(self, data):
        self.__data = [ '%s\n' % x for x in data.splitlines() ]
        self.__lcount = 0
    def readline(self):
        try:
            line = self.__data[self.__lcount]
            self.__lcount += 1
        except IndexError:
            line = ''
            self.__lcount = 0
        return line

