import sqlalchemy.orm

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


def debug_inline_params(stmt, bind=None):
    """Compiles a query or a statement and inlines bindparams.

    WARNING: Does not do any escaping."""
    if isinstance(stmt, sqlalchemy.orm.Query):
        if bind is None:
            bind = stmt.session.get_bind(stmt._mapper_zero_or_none())
        stmt = stmt.statement
    else:
        if bind is None:
            bind = stmt.bind 

    compiler = bind.dialect.statement_compiler(bind.dialect, stmt)
    compiler.bindtemplate = "%%(%(name)s)s"
    compiler.compile()
    return compiler.string % dict((k,repr(v)) for k,v in compiler.params.items())
