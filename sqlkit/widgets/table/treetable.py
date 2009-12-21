# Copyright (C) 2009, Sandro Dentella <sandro@e-den.it>
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
SqlTreeView
-----------

A widget that allows you to organize records in trees
"""
import gtk
from sqlkit import _
from table import SqlTable

class Header(object):

    def __init__(self, master, field_name, value):

        self.master = master
        value = self.master.gui_fields[field_name].get_human_value(value)
        setattr(self, field_name, value)
        
    def __getattribute__(self, name):

        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None

class SqlTreeTable(SqlTable):

    def __init__(self, tree_field_name=None, *args, **kwargs):

        SqlTable.__init__(self, *args, **kwargs)
        self.tree_field_name = tree_field_name
        self.treeview.set_reorderable(True)
        self.modelstore = gtk.TreeStore(object)
        self.treeview.set_model(self.modelstore)

    def fill_model(self):
        """
        fill the modelstore starting from an empty one and a self.records already complete.
        """
        
        parents = {}
        for record in self.records:
            field_value = getattr(record, self.tree_field_name)
            parent = parents.get(field_value, None)
            if not parent:
                try:
                    header = self.tree_make_header(field_value)
                    parent = parents[field_value] = self.modelstore.append(parent, [header])
                except AttributeError:
                    pass
            iter = self.modelstore.append(parent, [record])
            if field_value not in parents:
                parents[field_value] = iter

    def tree_make_header(self, field_value):

        return Header(self, self.tree_field_name, field_value)

    def key_tree_Down(self, treeview, event, data):
        """
        Liststores have the addon that a Down arrow can generate a new line while in treestores
        it's too difficoult to make out the next line and I leave to gtk that work
        """

        return False
    
