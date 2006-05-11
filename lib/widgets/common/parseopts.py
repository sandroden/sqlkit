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
            return join_tables(tables, engine=master.engine)

def inspect_mapper(mapper, noup=None, mode=None):
    # A mapper created using .join or .outerjoin from one table
    if isinstance(mapper.primarytable, sqlalchemy.sql.Join):
        m=inspect.InspectJoinMapper(mapper, noup=noup, mode=mode)
    # A mapper of a single table or a mapper creater with 'properties' option
    # tat results in a Lazy/Eager load  one
    else:
        m=inspect.InspectMapper(mapper, noup=noup, mode=mode)
    return m

def join_table_old(tables, engine=None, master=None,  mode='outer'):
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

def join_tables(tables, engine=None, master=None,  mode='outer'):
    """ join two or more tables in a mapper sqlalchemy.sql.Join
    mode: inner | outer
    """
    class JoinAuto(object): pass
    j = None
    t1 = tables[0]
    for t in tables[1:]:
        if j:
            t1 = j
        j = join2tables(t1, t, engine=engine, mode=mode)
        #dbg.write("j    ",j)
        ## j may be a tuple: join, Table1, Table2
        if isinstance(j, list):
            j = j[0]
        #dbg.write("j dopo    ", j)
    m = mapper(JoinAuto, j)
    return m

def join2tables(t1, t2, engine, mode='outerjoin'):
    """return a join of 2 tables. Accept strings or sqlalchemy.Table"""
    tbl = {}
    ## 
    if isinstance(t1, str):
        T1_ret = True
        T1 = Table(t1, engine=engine, autoload=True)
    else:
        T1_ret = False
        T1 = t1

    if isinstance(t2, str):
        T2_ret = True
        T2 = Table(t2, engine=engine, autoload=True)
    else:
        T2_ret = False
        T2 = t2

    join_cnd = inspect.get_join_cnd([ T1, T2 ] )
    #dbg.write("join condition (%s -%s): %s" % (T1, T2, join_cnd))
    if mode in ('outerjoin', 'outer'):
        j = T1.outerjoin(T2, and_(*join_cnd))
    else:
        j = T1.join(T2, *join_cnd)

    ret = [j]
    if T1_ret:
        ret += [T1]
    if T2_ret:
        ret += [T2]
        
    return ret
    

# join = user_table.outerjoin(
#         mail_table,
#         user_table.c.user_id == mail_table.c.mail_user_id
#         )
# m = Join.mapper = mapper(
#     Join, join, primary_key=[user_table.c.user_id])

    
    
