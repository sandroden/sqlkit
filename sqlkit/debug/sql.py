def get_create_statement(meta, typ='postgres'):
    """
    return the create statement of a
    obj may be a table or a metadata
    """
    from sqlalchemy import create_engine, Table
    from StringIO import StringIO
    
    buf = StringIO()
    engine = create_engine("%s://" % typ, strategy='mock',
                           executor=lambda s, p='': buf.write(s + p))

    meta.create_all(engine)
    return buf.getvalue()
