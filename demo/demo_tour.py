import os
import re
import gtk
import gobject
import pango
from sqlkit.layout import Layout, layout
from sqlkit import debug as dbg
# use for simple syntax highlighting ;-)
import tokenize
import keyword

(
   TITLE_COLUMN,
   MODULE_COLUMN,
   FUNC_COLUMN,
   ITALIC_COLUMN,
   MAPPED,
) = range(5)
CHILDREN_COLUMN = 3

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



class Demo(object):
    def __init__(self, pattern=".+.py$", xml=True):

        lay = """
           {B m=_File   } # {O t=quit}
           {v 
               {h TVS=a:120.300 {N TXS=txt:250. TVS=tree TVS=el TVS=pack TXS=xml} }
               TXS=note
            } 
        """

        self.l = Layout(lay, opts="s", title="Esempi" , geom=(600,700))

        self.l.notebook('N.0', ['src','tree', 'widget properties','pack properties','xml'])
        self.w = self.l.show(x='q')
        if not xml:
            self.w['N.0'].remove_page(-1)

        tx_src  = self.w['TX=txt']
        tx_note = self.w['TX=note']
        tx_xml = self.w['TX=xml']
        self.src  = tx_src.get_buffer()
        self.xml =  tx_xml.get_buffer()
        self.configure_buffer(self.src)
        self.note = tx_note.get_buffer()

        self.tv_tree = self.w['TV=tree']
        self.create_widget_tree(new=True, toplevel = self.w['Window'])
        self.ts_el   = self.prepare_treeview_elem(self.w['TV=el'])
        self.ts_pack = self.prepare_treeview_tree(self.w['TV=pack'])


        demos, child_demos = self.create_demos(pattern)

        self.tv = self.w['TV=a']
        ex = self.configure_treeview(self.tv, demos, self.src, self.note)


        self.l.menu('m=_File',
            ('inspect widgets' , 'activate', self.pop_inspect, ),
            ('gtk-quit' , 'activate', gtk.main_quit, ),
            )   

    def configure_treeview(self, treeview, testgtk_demos, src, note):
        model = gtk.TreeStore(
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_BOOLEAN,
        )

        treeview.set_model(model)
        selection = treeview.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        treeview.set_size_request(200, -1)

        for module in testgtk_demos:
            iter = model.append(None)
            model.set(iter,
                TITLE_COLUMN, module[TITLE_COLUMN],
                MODULE_COLUMN, module[MODULE_COLUMN],
                FUNC_COLUMN, module[FUNC_COLUMN],
                ITALIC_COLUMN, False,
                MAPPED, False
            )

            try:
                children = module[CHILDREN_COLUMN]
                for child_module in children:
                    child_iter = model.append(iter)
                    model.set(child_iter,
                        TITLE_COLUMN, child_module[TITLE_COLUMN],
                        MODULE_COLUMN, child_module[MODULE_COLUMN],
                        FUNC_COLUMN, child_module[FUNC_COLUMN],
                        ITALIC_COLUMN, False,
                        MAPPED, False
                    )
            except IndexError:
                pass

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Widget", cell, text=TITLE_COLUMN)
        treeview.append_column(column)
        selection.connect('changed', self.selection_changed_cb)

        treeview.expand_all()
        treeview.show_all()
        return model


    def selection_changed_cb(self, selection):
        model, iter = selection.get_selected()
        if model.iter_has_child(iter):
            return

        if not iter:
            return False

        name = model.get_value(iter, MODULE_COLUMN)
        self.load_module(name, self.src, self.note)
        self.l.sb("file: %s.py" % name)

    def load_module(self, name, asrc, anote):
        # set last_layout_object
        file_name = name + ".py"
        doc, body = self.readexample(file_name)

        ### fill text: src, notes, and xml
        self.insert_source(body, self.src)
        self.note.set_text(doc)

        ### exec the example
        GLOB = {'Layout': Layout, 'layout': layout, 'gtk': gtk}
        execfile(file_name, GLOB)

        self.xml.set_text(GLOB['l'].xml())
        self.last_lo = GLOB['l']
        self.last_w  = GLOB['w']
        self.prepare_treestore_for_elements(GLOB['l'].elements)
        self.create_widget_tree(toplevel=GLOB['w']['Window'])
        GLOB['w']['Window'].set_title(file_name)
        self.w['Window'].set_title("Esempio: %s" % (file_name))

    def prepare_treestore_for_elements(self, elements):
        tv = self.w['TV=el']
        ts = self.ts_el
        ts.clear()
        for el, val in elements.iteritems():
            if not isinstance(val, int):
                iter = ts.append(None)
                ts.set(iter, 0, el, 1, val.gtkClass)
                # properties
                for p,v in val.properties.iteritems():
                    child_iter = ts.append(iter)
                    ts.set(child_iter, 2, p, 3, v)

        ts = self.ts_pack
        ts.clear()
        for el, val in elements.iteritems():
            if not isinstance(val, int):
                iter = ts.append(None)
                ts.set(iter, 0, el, 1, val.container_flag, 2, val.gtkClass)
                # PACK properties
                for p,v in val.pack_properties.iteritems():
                    child_iter = ts.append(iter)
                    ts.set(child_iter, 3, p, 4, v)


    def prepare_treeview_elem(self, tv):
        tv.set_rules_hint(True)
        selection = tv.get_selection()
        selection.connect('changed', self.selection_changed_prop_cb)
        ts = gtk.TreeStore(str,str, str, str)
        tv.set_model(ts)

        ## TreeViewColumn & CellRenderer
        heads = ['elem', 'class', 'property', 'value' ]
        for i, v in enumerate(heads):
            tvc = gtk.TreeViewColumn(v, gtk.CellRendererText(), text=i)
            tvc.set_sort_column_id(i)
            tv.append_column(tvc)

        return ts

    def prepare_treeview_tree(self, tv):
        tv.set_rules_hint(True)
        ts = gtk.TreeStore(str, str, str, str, str)
        tv.set_model(ts)

        ## TreeViewColumn & CellRenderer
        heads = ['elem', 'container', 'class', 'property', 'value' ]
        for i, v in enumerate(heads):
            tvc = gtk.TreeViewColumn(v, gtk.CellRendererText(), text=i)
            tvc.set_sort_column_id(i)
            tv.append_column(tvc)


        return ts

    def selection_changed_prop_cb(self, selection):
        model, iter = selection.get_selected()
        if not iter:
            return False

        ## get the class name, position 1
        el_key = model.get_value(iter, 0)
        class_name = model.get_value(iter, 1)
        data = []

        for prop in gobject.list_properties(class_name):
            el = self.last_lo.elements[el_key]
            try:
                val_lay = el.properties[prop.name]
            except KeyError:
                val_lay = None

            try:
                val_gtk = self.last_w[el_key].get_property(prop.name)
            except TypeError:
                val_gtk = None
            data.append((prop.name, prop.nick, prop.value_type, val_gtk, val_lay))
        TreeShow(data)

    def pop_inspect(self, *args):
        dbg.gtk_dbg.show_widgets()

    def create_demos(self, pattern=None):
        ### taken from __init__.py demos dir 
        file_list = [x for x in os.listdir('.') if re.match(pattern, x)]

        demo_list = []
        file_list.sort()
        for mod in file_list:
            # Leave underscored Modulnames.
            if re.match('[_A-Z]',mod):
                continue
            mod = mod[:-3]
            txt, body = self.readexample(mod + ".py")
            if body:
                _description = txt.splitlines()[0]
                demo_list.append((_description, mod))

        child_demos = {}
        testgtk_demos = []

        def beauty(m):
            return m.group(1)[0].isupper() and m.group(1) or m.group(1).capitalize()

        D_TEMPL ="%sDemo"
        for descr, mod in demo_list:
            # Find some categorized demos
            try:
                main, child = descr.split('/')
            except ValueError:
                # No, only one application
                demo_class = D_TEMPL % re.sub('(\S+) *', beauty, descr)
                testgtk_demos.append((descr, mod, demo_class))

            else:
                # Ok. Some more testing
                demo_class = D_TEMPL % re.sub('(\S+) *', beauty, child)

                try:
                    # Applicationgroup already defined?
                    child_demos[main.upper()].append((child, mod, demo_class))
                except KeyError:
                    # No. Start a new category
                    child_demos.setdefault(main.upper(), []).append((child, mod, demo_class))
                    testgtk_demos.append((main, None, None, child_demos[main.upper()]))


        return (testgtk_demos, child_demos)




    def create_widget_tree(self, new=False, toplevel=None):
        global show_widgets
        global model
        if new:
            show_widgets = dbg.gtk_dbg.show_widgets(lay=False)
            model = show_widgets.create_model(self.tv_tree)

        show_widgets.fill_model(toplevel, model)
        self.tv_tree.expand_all()

# def fillBuf(buf, file=None, txt=None):
#     if file:
#         idf = open(file,"r")
#         txt = idf.read()
#         idf.close()

#     buf.set_text(txt)

# def txt2buf(tx_note, txt):
#     buf.set_text(txt)


    def insert_source(self, data, buf):
        buf.delete(*buf.get_bounds())
        iter = buf.get_iter_at_offset(0)
        #print buf.get_tag_table()
        last_erow, last_ecol = 0, 0
        was_newline = False # multiline statement detection
        for x in tokenize.generate_tokens(InputStream(data).readline):
            # x has 5-tuples
            tok_type, tok_str = x[0], x[1]
            srow, scol = x[2]
            erow, ecol = x[3]

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
                continue
            elif tok_type == tokenize.NAME:
                if tok_str in keyword.kwlist:
                    buf.insert_with_tags_by_name(iter, tok_str, 'source', 'keyword')
                    continue
            elif tok_type == tokenize.STRING:
                buf.insert_with_tags_by_name(iter, tok_str, 'source', 'string')
                continue

            # No special format for use. Check for newline.
            was_newline = tok_type in (tokenize.NEWLINE, tokenize.NL)
            buf.insert_with_tags_by_name(iter, tok_str, 'source')

    def configure_buffer(self, buf):
        #print "Configuro %s" % buf
        tag = buf.create_tag('title')
        tag.set_property('font', 'Sans 18')

        tag = buf.create_tag('source')
        tag.set_property('font', 'monospace')
        tag.set_property('pixels_above_lines', 0)
        tag.set_property('pixels_below_lines', 0)
        tag = buf.create_tag('keyword', foreground='#00007F',
                                weight=pango.WEIGHT_BOLD)
        tag = buf.create_tag('string', foreground='#007F00')
        tag = buf.create_tag('comment', foreground='#7F007F',
                                       style=pango.STYLE_ITALIC)


    def readexample(self, file_name):
        """ read the __doc__ of the example and separate it from the body"""

        idf = file(file_name,'r')
        txt = idf.read()
        idf.close()
        pat = re.compile(r'''
        ^"""(?:(?P<doc>[^"]*)""")\s*(?P<body>(.*))
        ''', re.MULTILINE| re.DOTALL|re.VERBOSE)
        m = pat.search(txt)
        if m:
            return  m.group('doc','body')
        else:
            return (None, None)


class TreeShow(object):
    def __init__(self, data):
        l = layout.Layout( "TVS=a", opts="Vs")
        w = l.show()
        tv = w['TV=a']

        ts = gtk.ListStore(str, str, str, str, str)
        tvc = gtk.TreeViewColumn('prop', gtk.CellRendererText(),text=0)
        tvc.set_sort_column_id(0)
        tv.append_column(tvc)
        
        cell = gtk.CellRendererText()
        #cell.set_property('style', pango.STYLE_BOLD)
        tvc = gtk.TreeViewColumn('lay val', cell, text=4)
        tvc.set_sort_column_id(4)
        tv.append_column(tvc)

        cell = gtk.CellRendererText()
        cell.set_property('style', pango.STYLE_ITALIC)
        tvc = gtk.TreeViewColumn('gtk val', cell, text=3)
        tvc.set_sort_column_id(3)
        tv.append_column(tvc)

        cell = gtk.CellRendererText()
        cell.set_property('style', pango.STYLE_ITALIC)
        tvc = gtk.TreeViewColumn('nick', cell, text=1)
        tvc.set_sort_column_id(1)
        tv.append_column(tvc)


        tv.set_model(ts)
        for i in data:
            iter = ts.append(None)
            ts.set(iter, 0, i[0], 1, i[1],  2, i[2],
                   3, i[3],  4, i[4])
