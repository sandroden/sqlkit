from sqlkit.widgets.common import sqlwidget

class TotalObj(object):
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

    def get_bgcolor(self, field_name):
        """return color for column field_name
        Normally none unless one of the totals columns
        """
        return getattr(self, field_name) and self._color

    def get_fgcolor(self, field_name):
        """return color for column field_name
        Normally none unless one of the totals columns
        """
        if getattr(self, field_name) is None:
            return None
        else:
            return self._fg_color
        

class Totals(object):
    """
    An object whose 'compute' method adds TotalObjets to show
    partial totals/grand totals to a table.
    A TotalObject is inserted each time total_by changes.
    If total_by is a callable, it's evaluated to detect if a partial total
    must be inserted
    """
    def __init__(self, table):
        self.table = table
        self.totals = {}
        self.subtotals = {}
        self.brake_func = None
        self.prev = None

    def add_total(self, field_name):
        """
        Add a total object each time subtotal changes
        """

        if not self.table.get_field_type(field_name) in sqlwidget.NUMBERS:
            raise NotImplemented("%s is not a number" % field_name)
        self.totals[field_name] = 0
        self.subtotals[field_name] = 0
        self.compute()
            
    def del_total(self, field_name):
        del self.totals[field_name]

    def add_brake(self, func, *args):
        """
        if func is a string,  is taken as a field_name, any change on that field value
        will trigger a subtotal via brake_func

        If func is a function it will be set as brake_function with arguments args
        """
        if isinstance(func, (str, unicode)):
            field_name = func
            def subtotal_diff(obj):
                return getattr(obj, field_name)
            self.brake_func = subtotal_diff
        else:
            print "FUNC", func, type(func)
            raise NotImplementedError
        self.compute()

    def is_different(self, obj):
        if self.prev is None:
            self.prev = self.brake_func(obj)
            return False
        
        if self.prev != self.brake_func(obj):
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
        tot = TotalObj(self.table.field_list, sub=sub)
        if after:
            piter = self.table.liststore.insert_after(row.iter)
        else:
            piter = self.table.liststore.insert_before(row.iter)            
        self.table.liststore.set_value(piter, 0, tot)
        return tot

    def insert_subtotal(self, row, after=False):
        tot = self.insert(row, after=after, sub=True)
        for field_name in self.totals:
            setattr(tot, field_name, self.subtotals[field_name])
            
    def insert_total(self, row, after=False):
        tot = self.insert(row, after=after, sub=False)
        for field_name in self.totals:
            setattr(tot, field_name, self.totals[field_name])
            
    def remove(self, row):
        self.table.liststore.remove(row.iter)
        
    def compute(self):
        if not self.totals.keys():
            return
        if not self.table.records:
            return
        
        self.initialize()
        for row in self.table.liststore:
            obj = self.table.liststore[row.path][0]
            if isinstance(obj, TotalObj):
                self.remove(row)
            else:
                if self.brake_func and self.is_different(obj):
                    self.insert_subtotal(row)
                    self.prev = self.brake_func(obj)
                    self.reset_subtotals()
                self.sum(obj)
                
        self.insert_total(row, after=True)
        if self.brake_func:
            self.insert_subtotal(row, after=True)
        
