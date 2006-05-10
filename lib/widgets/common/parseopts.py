from sqlalchemy import *
import sqlkit.inspect as inspect
import dbg.gtk_dbg


def get_mapper(master, mapper_obj, tables):
    """If no mapper is provided it will be built from the table"""

    if mapper_obj:
        return mapper_obj

    elif tables:
        if isinstance(tables, str) or  len(tables) == 1:
            name = "%s_class" % (tables)
            sa_table = Table(tables, engine=master.engine, autoload=True)
            X = type(name, (object,), {})
            m = mapper(X, sa_table)
            return m
        else:
            return join_table(tables, engine=master.engine)

def inspect_mapper(mapper, noup=None, mode=None):
    # A mapper created using .join or .outerjoin from one table
    if isinstance(mapper.primarytable, sqlalchemy.sql.Join):
        m=inspect.InspectJoinMapper(mapper, noup=noup, mode=mode)
    # A mapper of a single table or a mapper creater with 'properties' option
    # tat results in a Lazy/Eager load  one
    else:
        m=inspect.InspectMapper(mapper, noup=noup, mode=mode)
    return m

def join_table(tables, engine=None, master=None,  mode='outer'):
    """ join two or more tables in a mapper sqlalchemy.sql.Join
    mode: inner | outer
    """
    class JoinAuto(object): pass

    if not engine:
        engine=master.engine
        
    tbl = {}
    for tbl_name in tables:
        tbl[tbl_name] = Table(tbl_name, engine=engine, autoload=True)

    T0 = tbl[tables[0]]
    T1 = tbl[tables[1]]

    join_cnd = inspect.get_join_cnd([ T0, T1 ] )
    J = T0.outerjoin(T1, *join_cnd)
    m = mapper(JoinAuto, J)
    return m

def join2tables(t1, t2, engine, mode='outerjoin'):
    """return a join of 2 tables. Accept strings or sqlalchemy.Table"""
    tbl = {}
    ## 
    if isinstance(t1, str):
        T1 = Table(t1, engine=engine, autoload=True)
    else:
        T1 = t1

    if isinstance(t2, str):
        T2 = Table(t2, engine=engine, autoload=True)
    else:
        T2 = t2

    join_cnd = inspect.get_join_cnd([ T1, T2 ] )
    if mode in ('outerjoin', 'outer'):
        return T1.outerjoin(T2, *join_cnd)
    else:
        return T1.join(T2, *join_cnd)
        
    

# join = user_table.outerjoin(
#         mail_table,
#         user_table.c.user_id == mail_table.c.mail_user_id
#         )
# m = Join.mapper = mapper(
#     Join, join, primary_key=[user_table.c.user_id])

    
    
