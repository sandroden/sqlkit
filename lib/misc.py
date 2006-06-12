import gtk

class EasyTreeView(object):
    def __init__(self, cols, tv=None, model=None):
        if tv:
            self.tv = tv
        else:
            self.l = self._get_layout()
            self.w = self.l.show()
            self.tv = self.w['TV=a']
            self.l.connect(('tb=gtk-quit', 'clicked',
                            lambda l: self.w['Window'].destroy()))

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
                self.tvc[i] = gtk.TreeViewColumn(col, cell(), active=i)
            else:
                self.tvc[i] = gtk.TreeViewColumn(col, cell(), text=i)
            self.tvc[i].set_sort_column_id(i)
            self.tv.append_column(self.tvc[i])


