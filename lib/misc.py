import gtk
import layout

class EasyTreeView(object):
    def __init__(self, cols, tv=None, model=None, sort=True,
                 resize=True, show=True, but=''):
        if tv:
            self.tv = tv
        else:
            self.l = self._get_layout(but)
            self.l.prop('Window', 'visible', show)
            self.w = self.l.show()
            self.tv = self.w['TV=a']
            
            self.l.connect(
                ('tb=gtk-quit', 'clicked', lambda l: self.w['Window'].destroy()),
                )

        self.columns = []
        self.column_names = []
        for col in cols:
            if isinstance(col, str):
                self.column_names += [col]
                self.columns += [str]
            if isinstance(col, tuple):
                # the second position is for type
                self.column_names += [col[0]]
                self.columns += [col[1]]

        if not model:
            self.model = gtk.TreeStore(*self.columns)
        else:
            self.model = model
            
        self.tv.set_enable_search(True)
        self.tv.set_model(self.model)
        self.tvc = {}
        for i, col in enumerate(self.column_names):
            cell = gtk.CellRendererText
            if self.columns[i] == bool:
                cell = gtk.CellRendererToggle
                self.tvc[col] = gtk.TreeViewColumn(col, cell(), active=i)
            else:
                self.tvc[col] = gtk.TreeViewColumn(col, cell(), text=i)
            if sort == True:
                self.tvc[col].set_sort_column_id(i)
            self.tvc[col].set_resizable(resize)
            self.tv.append_column(self.tvc[col])

    def show(self):
        self.w['Window'].show_all()

    def _get_layout(self, but):
        lay = """
          {O tb=gtk-quit  tb=gtk-clear %s}
          TVS=a
        """ % (but)
        #dbg.write()
        return layout.Layout(lay, opts="s")


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

