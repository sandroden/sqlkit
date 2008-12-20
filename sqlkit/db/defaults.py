import datetime
import sqlalchemy

tables = {}

def set_default(table_name, tbl_dict):
    """Add a dictionary with one entry for each field of a table
    """
    global tables
    if table_name in tables:
        tdict = tables[table_name]
        tdict.update(tbl_dict)

    else:
        tables[table_name] = tbl_dict

class Defaults(object):

    def __init__(self, table_name, metadata=None):
        self.table_name = table_name
        self.metadata = metadata
#         if metadata:
#             self.table = metadata.tables[table_name]

    def set_defaults(self, tbl_dict):
        global tables
        if self.table_name in tables:
            tdict = tables[self.table_name]
            tdict.update(tbl_dict)

        else:
            tables[self.table_name] = tbl_dict

    def set_default(self, field_name, value):
        tbl_dict = {field_name: value}
        self.set_defaults(tbl_dict)

    def fk(self, field_name, attr, value):
        ## when we define defaults, metadata may not yet have loaded the table
        ## let's delay the moment...
        def get_by_description():
            from sqlkit.db.minspect import get_foreign_info
            from sqlalchemy.sql import select            

            global tables
            table = self.metadata.tables[self.table_name]
            col = table.columns.get(field_name)
            fkey = col.foreign_keys
            fk_table, fk_col = get_foreign_info(fkey, names=False)
            s = select([fk_col], getattr(fk_table.c, attr) == value)
            conn = self.metadata.bind.connect()
            result = conn.execute(s)
            row = result.fetchone()
            if row:
                tables[self.table_name][field_name] = row[fk_col.name]
            else:
                tables[self.table_name][field_name] = None
            return tables[self.table_name][field_name]
        
        self.set_default(field_name, get_by_description)
    
    today = datetime.date.today
    now = datetime.datetime.now


def get_default(table_name, field_name):
    """
    Return the default value for a field_name
    if the value is a callable... call it
    """
    if isinstance(table_name, sqlalchemy.Table):
        table_name = table_name.name
        
    try:
        value = tables[table_name][field_name]
        if callable(value):
            return value()
        else:
            return value
        
    except KeyError, e:
        pass

    

