import datetime
import sqlalchemy

tables = {}
hooks = {}
layout_dict = {}

def set_default(table_name, tbl_dict):
    """
    Add a dictionary with one entry for each field of a table
    """
    global tables
    if table_name in tables:
        tdict = tables[table_name]
        tdict.update(tbl_dict)

    else:
        tables[table_name] = tbl_dict

class Defaults(object):

    def __init__(self, table_name, metadata=None, local=False):
        self.table_name = table_name
        self.metadata = metadata
        self.local = local
        if local:
            self.tdict = {}
        else:
            global tables
            if self.table_name in tables:
                self.tdict = tables[self.table_name]
            else:
                self.tdict = tables[self.table_name] = {}

    def set_defaults(self, tbl_dict):
        """
        set defaults using a dict as input
        """
        if self.table_name in tables:
            self.tdict = tables[self.table_name]
            self.tdict.update(tbl_dict)

        else:
            tables[self.table_name] = tbl_dict

    def set_default(self, **kw):
        """
        set a single default
        """
        for field_name, value in kw.iteritems():
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
        
        self.set_defaults( {field_name : get_by_description})
    
    today = datetime.date.today
    now = datetime.datetime.now


    def get(self, field_name):
        """
        Return the default value for a field_name
        if the value is a callable... call it
        """
        try:
            value = self.tdict[field_name]
            if callable(value):
                return value()
            else:
                return value

        except KeyError, e:
            return get_default(self.table_name, field_name)

def get_default(table_name, field_name):
    """
    Return the default value for a field_name
    if the value is a callable... call it
    """
    if isinstance(table_name, sqlalchemy.Table):
        table_name = table_name.name
        
    try:
        value = tables[table_name][field_name]
    except KeyError, e:
        return

    if callable(value):
        return value()
    else:
        return value

    


def register_hook(table, hook):
    """
    Register a hook for table. Each time a sqlwidget is instantiated for the table
    a hook is searched for here to initialize the sqlwidget

    :param table: a table for which we want to register the hook
    :param hook: the hook to be registered (a class or an instance)

    """
    from inspect import isclass

    global hooks
    
    if isinstance(table, sqlalchemy.Table):
        table_name = table.name
    else:
        table_name = table
        
    if not isclass(hook):
        hook = hook.__class__
    
    hooks[table_name] = hook

def get_hook(table, instance=False):
    """
    Return a hook tor table or None

    :param table: the table for which we want the hook
    :param instance: a boolean: True is we want an instance False if we want the class
    """
    
    if isinstance(table, sqlalchemy.Table):
        table_name = table.name
    else:
        table_name = table

    hook = hooks.get(table_name, None)
    if hook and  instance:
        hook = hook()
    return hook

def get_table_name(table):
    """
    return a table name. input may be a tablename or a sqlalchemy.Table
    """

    if isinstance(table, sqlalchemy.Table):
        table_name = table.name
    else:
        table_name = table

    return table_name

def register_layout(table, layout, nick='default', persistent=False):
    """
    Register a layout for table with a nick (default nick is 'default')
    Each time a sqlwidget is instantiated for the table
    a layout is searched for here 

    :param table: the table to register the layout for. May be a sqlakchemy.Table or a string
    :param layout: the layut to be registered
    :param nick: the name of a nick to use for this layout (used for SqlMask(... nick=nick)
    :param persistent: register in the _sqlkit tables (not yet implemented)
    """

    global layout_dict

    table_name = get_table_name(table)
    table_layout_dict = layout_dict.get(table_name, {})
    table_layout_dict[nick] = layout
    layout_dict[table_name] = table_layout_dict

    if persistent:
        raise NotImplementedError("registering of layout is not yet implemented")


def get_layout(table, nick='default'):
    """
    Return a layout for table for nick 'nick'

    :param table: the table to register the layout for. May be a sqlakchemy.Table or a string
    :param nick: the nick used for this layout 
    
    """
    
    global layout_dict
    table_name = get_table_name(table)

    table_layout_dict = layout_dict.get(table_name, None)
    try:
        return table_layout_dict[nick]
    except (KeyError, TypeError), e:
        return None
