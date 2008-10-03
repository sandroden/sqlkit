from sqlkit.widgets.common.completion import SimpleCompletion, FkeyCompletion

class CellWidget(object):

    def __init__(self, field):
        self.field = field
        self.master = master = field.master
        self.field_name = field_name = field.field_name
        

        self.add_completion(master.is_fkey(field_name),
                            master.get_field_type(field_name))

        self.master.widgets[field_name] = self
        
    def fget(self):
        # CellWidget has an editable only if we're editing...
        if self.field_name == self.master.currently_edited_field_name:
            return self.master.editable
        else:
            raise NotImplementedError
    
    entry = property(fget)

    def add_completion(self, is_fkey, pytype):
        """completion is set just for fkey and string fields"""

        if is_fkey:
            Completion = FkeyCompletion
        elif pytype in (str, unicode):
            Completion = SimpleCompletion
        else:
            return
        
        self.completion = Completion(self.master, self, self.field_name)
        self.master.completions[self.field_name] = self.completion
        
    def set_value(self, value):
        self.master.set_value(self.field_name, value)

    def get_value(self, shown=False):
        return self.master.get_value(self.field_name)

    

