
import re
from sqlalchemy import Table, MetaData, sql
from sqlalchemy.orm import sessionmaker, mapper
from sqlkit.db import minspect

import dbg.gtk_dbg

class DbProxy(object):
    """
    A proxy do the database... it's meant to easy the way we pass information
    to the sqkwidget in the simpler situation:

    * if no metadata is passed, MetaData() will create it
    * if engine is passed it will be put in metadata as 'bind' attribute
    * if no session is passed a session is created via sessionmaker 

      db = proxy.DbProxy(engine='postgres://localhost/fossati')
      session = db.get_session()

    at that point sqlwidget will retrieve info this way::

      SqlTable(table="ticket_project", dbproxy=self.dbproxy)

    """
    def __init__(self, metadata=None, engine=None, Session=None):
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = MetaData()
            if engine:
                self.metadata.bind = engine

        if not Session:
            self.Session = sessionmaker(bind=self.metadata.bind,
                                        autocommit=False)
        else:
            self.Session = Session
            
    def get_session(self):
        return self.Session()

    def get_table(self, name):
        """return a sqlalchemy.Table object from a table_name.
        Uses self.metadata"""
        
        if name in self.metadata.tables:
            return self.metadata.tables[name]
        else:
            return Table(name, self.metadata, autoload=True)

    
    def get_mapper(self, mapper_obj, tables):
        """If no mapper is provided it will be built from the table(s)
        tables may be:
           a list of table_names
           a list of sqlalchemy.Tables
           a single table_name
           a single sqlalchemy.Table
           a string of table_names
        """
    
        if mapper_obj:
            return mapper_obj
    
        ## tables may be 'table1, table2, table3'
        if not isinstance(tables, list):
            tables = re.split('[ ,]+', tables)
            
        tables = [self.get_table(tbl) for tbl  in tables]

        if len(tables) == 1:
            return self.table2mapper(tables[0])
        else:
            return self.join_tables(tables)
    
    def table2mapper(self, table):
        name = "%s_class" % (table)
        if isinstance(table, str ):
            table = self.get_table(name)
            
        X = type(name, (object,), {})
        m = mapper(X, table)
        return m
        
    def join_tables(self, tables, master=None,  mode='outer'):
        """ join two or more tables in a mapper sqlalchemy.sql.Join
        mode: inner | outer
        """
        class JoinAuto(object): pass
        j = None
        t1 = tables[0]
        for t in tables[1:]:
            if j:
                t1 = j
            j = join2tables(t1, t, mode=mode)
            #dbg.write("j    ",j)
            ## j may be a tuple: join, Table1, Table2
            if isinstance(j, list):
                J = j[0]
            else:
                J = j
            #dbg.write("j dopo    ", j)
        if mode == 'outer':
    #        m = mapper(JoinAuto, J, primary_key=j[1].primary_key )
            m = mapper(JoinAuto, J)
        else:
            m = mapper(JoinAuto, J)
        #dbg.write(m)
        return m

    def join2tables(self, t1, t2, mode='outerjoin'):
        """return a join of 2 tables. Accept strings or sqlalchemy.Table"""
        tbl = {}
        ## 
        if isinstance(t1, str):
            T1_ret = True
            T1 = Table(t1, engine, autoload=True)
        else:
            T1_ret = False
            T1 = t1
    
        if isinstance(t2, str):
            T2_ret = True
            T2 = Table(t2, self.metadata, autoload=True)
        else:
            T2_ret = False
            T2 = t2
    
        join_cnd = minspect.get_join_cnd([ T1, T2 ] )
        #dbg.write("join condition (%s -%s): %s" % (T1, T2, join_cnd))
        if mode in ('innerjoin', 'inner'):
            dbg.write('join... non outer')
            j = T1.join(T2, and_(*join_cnd))
        else:
            dbg.write('outerjoin', T1, T2, join_cnd)
            j = T1.outerjoin(T2, *join_cnd)
    
        return j
         
    def inspect_mapper(self, mapper, noup=None, mode=None):
        """Return an instance of minspect.InspectMapper
        """
        # A mapper created using .join or .outerjoin from one table
    
        if isinstance(mapper.local_table, sql.Join):
            m=minspect.InspectJoinMapper(mapper, noup=noup, mode=mode)
        # A mapper of a single table or a mapper creater with 'properties' option
        # that results in a Lazy/Eager load  one
        else:
            m=minspect.InspectMapper(mapper, noup=noup, mode=mode)
        return m
