class CellWidget(object):

    def __init__(self, field):
        self.field = field
        self.master = field.master
        self.field_name = field.field_name
        self.initial_value = None

    def set_value(self, value):
        self.master.set_value(self.field_name, value)

    def get_value(self, shown=False):
        self.master.get_value(self.field_name)

    

