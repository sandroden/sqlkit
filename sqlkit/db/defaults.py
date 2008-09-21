tables = {}

def set_default(table_name, tbl_dict):
    """Add a dictionary with one entry for each field of a table
    """
    global tables
    if table_name in tables:
        tdict = tables[table_name]
        tdict.extend(tbl_dict)

    else:
        tables[table_name] = tbl_dict

def get_default(table_name, field_name):
    """
    Return the default value for a field_name
    if the value ais a callable... call it
    """
    try:
        value = tables[table_name][field_name]
        if callable(value):
            return value()
        else:
            return value
        
    except KeyError, e:
        pass

    

