from sqlkit.widgets.common import sqlwidget
from datetime import date, datetime
import dbg
import gtk

class TotalObj(object):
    """
    A simple class that represents the object holding the totals and a way to represent it

    personalization

    You can change the look of totals inheriting from TotalObj and placing the new class
    as ``class`` attribute of Totals
    """

    _sub_color = 'gray92'
    _total_color = 'gray80'
    _fg_color = 'indianred'
    def __init__(self, fields, sub=True):
        """
        all fileds will be initialized to None
        _sub will be set to Tue for subTotals, to render with different colors
        """
        for name in fields:
            setattr(self, name, None)
        if sub:
            self._color = self._sub_color
        else:
            self._color = self._total_color

    def set_value_and_colors(self, cell, value, field_name):
        """
        set the color cell and possibly background
        """
        if value is not None:
            cell.set_property('markup', "<b><i>%s</i></b>" % (value))
        
        # set color only if we have a value
        if getattr(self, field_name):
            cell.set_property('foreground', self._fg_color)
        

class Totals(object):
    """
    An object whose 'compute' method adds TotalObjets to show
    partial totals/grand totals to a table.
    A TotalObject is inserted each time total_by changes.
    If total_by is a callable, it's evaluated to detect if a partial total
    must be inserted
    """
    total_class = TotalObj

    def __init__(self, table):
        self.table = table
        self.totals = {}
        self.subtotals = {}
        self.break_func = None
        self.prev = None

    def add_total(self, *field_names):
        """
        Add a total object each time subtotal changes
        """
        for field_name in field_names:
            if not self.table.get_field_type(field_name) in sqlwidget.NUMBERS:
                raise NotImplementedError("%s is not a number" % field_name)
            self.totals[field_name] = 0
            self.subtotals[field_name] = 0
        self.compute()
            
    def del_total(self, field_name):
        del self.totals[field_name]

    def add_break(self, field_name, func=None):
        """
        If no ``func`` is provided, a break_func will be setup to insert a subtotal
        each time field_name changes.

        Othewise ``func`` will be set as break_function. Break function must have
        this signature::

           def break_func(obj, field_name)

        see ``func_date_*`` is this module for examples
           
        """
        if not func:
            def subtotal_diff(obj):
                return getattr(obj, field_name)
            self.break_func = subtotal_diff
        else:
            def subtotal_diff(obj):
                return func(obj, field_name)
            self.break_func = subtotal_diff
        self.compute()

    def add_date_break(self, field_name, period):
        """
        Set date break period can be: ``day``, ``week``, ``month``, ``quarter``, ``year``
        """
        func = globals()['func_date_same_%s' % period]
        self.add_break(field_name, func)

    def is_different(self, obj):
        if self.prev is None:
            self.prev = self.break_func(obj)
            return False
        
        if self.prev != self.break_func(obj):
            return True
        
        return False

    def initialize(self):
        self.prev = None
        for field_name in self.totals.keys():
            self.totals[field_name]    = 0
            self.subtotals[field_name] = 0
        
    def sum(self, obj):
        for field_name in self.totals.keys():
            self.totals[field_name]    += getattr(obj, field_name, 0) or 0
            self.subtotals[field_name] += getattr(obj, field_name, 0) or 0

    def reset_subtotals(self):
        for field_name in self.totals:
            self.subtotals[field_name] = 0

    def insert(self, row, after=None, sub=False):
        tot = self.total_class(self.table.field_list, sub=sub)
        if after:
            piter = self.table.liststore.insert_after(row.iter)
        else:
            piter = self.table.liststore.insert_before(row.iter)            

        self.table.liststore.set_value(piter, 0, tot)

        newrow = self.table.liststore[piter]
        return newrow, tot

    def insert_subtotal(self, row, after=False):
        row, tot = self.insert(row, after=after, sub=True)
        for field_name in self.totals:
            setattr(tot, field_name, self.subtotals[field_name])
        return row, tot
    
    def insert_total(self, row, after=False):
        if not row:
            row = self.table.liststore[-1]
        row, tot = self.insert(row, after=after, sub=False)
        for field_name in self.totals:
            setattr(tot, field_name, self.totals[field_name])
        return row
    
    def remove(self, row):
        self.table.liststore.remove(row.iter)
        
    def preserve_selection(func):
        def new_func(self):
            self.table.commit_inhibited = True
            selection = self.table.treeview.get_selection()
            model, rows = selection.get_selected_rows()
            if rows:
                path = rows[0]
                #remember = gtk.TreeRowReference(self.table.liststore, path)
            func(self)
            if rows:
                #selection.select_path(remember.get_path())
                selection.select_path(path)
            self.table.commit_inhibited = False
        new_func.__doc__ = func.__doc__
        return new_func

    @preserve_selection
    def compute(self):
        """
        Go, add subtotals and total
        """
        if not self.totals.keys():
            return
        if not self.table.records:
            return
        
        self.initialize()
        for row in self.table.liststore:
            obj = self.table.liststore[row.path][0]
            if isinstance(obj, self.total_class):
                self.remove(row)
            else:
                if self.break_func and self.is_different(obj):
                    self.insert_subtotal(row)
                    self.prev = self.break_func(obj)
                    self.reset_subtotals()
                self.sum(obj)

        row = self.insert_total(row=None, after=True)
        if self.break_func:
            self.insert_subtotal(row, after=False)
        
def func_date_same_day(obj, field_name):
    date = getattr(obj, field_name)
    if isinstance(date, datetime):
        return date.date()
    else:
        return date

def func_date_same_week(obj, field_name):
    date = getattr(obj, field_name)
    #print date, date.year, getattr(obj, field_name).strftime('%U')
    return date.year, getattr(obj, field_name).strftime('%U')

def func_date_same_month(obj, field_name):
    date = getattr(obj, field_name)
    return date.month, date.year

def func_date_same_year(obj, field_name):
    return getattr(obj, field_name).year

def func_date_same_quarter(obj, field_name):
    date = getattr(obj, field_name)
    return date.year, divmod(date.month -1, 3)[0]


