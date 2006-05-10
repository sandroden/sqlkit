#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import sqlkit as sk
import sqlkit.inspect as inspect
import dbg 
dbg.DBG = 1

from sqlalchemy import *
from layout import *
#from validator import Validator

engine = sk.config.spawnEngine(echo=False)
map_labels(filename='label_map.txt')

def join_tables(tables, engine=None, master=None,  mode='outer'):
    """ join two or more tables in a mapper sqlalchemy.sql.Join
    mode: inner | outer
    """
    global J, join_cnd
    class JoinAuto(object): pass

    if not engine:
        engine=master.engine
        
    tbl = {}
    for tbl_name in tables:
        tbl[tbl_name] = Table(tbl_name, engine=engine, autoload=True)

    T0 = tbl[tables[0]]
    T1 = tbl[tables[1]]

    join_cnd = inspect.get_join_cnd([ T0, T1 ] )
    dbg.write("join_cnd", join_cnd, "T0", type(T0), "T1", type(T1))

    J = T0.outerjoin(T1, join_cnd[0])
    #T0.c.user_id == T1.c.mail_user_id
    print "CASSO", J
    print "J %s" % J
    #dbg.write("J", J)

    dbg.write('mapper(%s, %s)' % (JoinAuto, J))

    m = mapper(JoinAuto, J)
    return m


#m = join_tables(tables=['euro_user', 'euro_mail'], engine=engine)

zz = sk.mask.SqlMask (sql="user_id > 5",
                      tables=['euro_user', 'euro_mail'], engine=engine)

#zz.sqlData.printall(mode='dict')

gtk.main()


