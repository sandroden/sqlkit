####### SqlData
# pointer: this is a key element to retrieve a mapper (as iter in a treeview)
# pointer is a list whose length depends on how may properties are there
# connecting to other ClassObject (rows)
# the order in which 

import sys
import sqlalchemy
# from mapper import *
# import mapper
sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path, sd
import reflect

ONETOMANY=0

class SqlData(object):
    """main data manipulation interface
    """
    pointer_info = None
    index = None  # dict of all pointers

    def __init__(self, res_obj, mapper_info, left=True, fields=None):
        self.res_obj = res_obj
        self.mapper_info = mapper_info
        self.create_index(left=left)
        self.current = 0
        if not fields:
            fields = mapper_info.fields
        self.field_list = fields
        
        tables = mapper_info.tables()
        #for t in tables:
        #    sd.debug("Table: %s => %s" % (t, mapper_info.table_fields(t)))
        
        
    def next(self, mode='dict', fields=None):
        return self.get(mode=mode, fields=fields, incr = 1)

    def prev(self, mode='dict', fields=None):
        self.get(mode=mode, fields=fields, incr = -1)

    def get(self, index=None, mode='dict', fields=None, incr=0):
        """return a dictionary field_name:value corresponding to
        the next tuple (row) in res_obj. Keep a pointer to the row.
        mode can be 'values', only values will be printed (debug only)
        Fields may be a list (as per self.fields)
        """
        R = {}
        if index:
            self.current = index
        self.current += incr
        try:
            idx = self.index[self.current]
        except IndexError:
            self.current -= 1
            return
        #sd.debug("current: %s - %s" % (self.current, idx ))
        

        row = self.res_obj[idx[0]]
        #print row.c.keys()
        for key in row.c.keys():
            R[key] = getattr(row, key)
            
        ## FIXME: queste righe funzionano solo per un mapper in cascata
        ## serve una ricorsione per il caso generale
        for prop in self.mapper_info.props:
            row_list = getattr(self.res_obj[idx[0]], prop[0])
            row = row_list             ### MANYTOONE
            if prop[1] == ONETOMANY:
                if not self.left:
                    row = row_list[idx[1]]
                else:
                    try:
                        row = row_list[idx[1]]
                    except IndexError:
                        pass


            try:
                for key in row.c.keys():
                    R[key] = getattr(row, key)
            except:
                pass

        if fields == None:
            fields = self.field_list

        if mode == 'dict':
            ret = {}
            for field in fields:
                ret[field] = R[field]
            return ret
        else:
            ## let us respect the order
            return [R[f] for f in fields if f in R]

    def all(self):
        """print all the records"""
        pass

    def fields(self, fields):
        """sets the list of fields that will be returned"""
        self.field_list = fields

    def update(self, row={}, pointer=None):
        """receive a pointer to a row and a dict whose keys are the field_name
        and whose values are the new values and UPDATE the corresponding
        row_obj.
        Check that all primary keys are contained in the row.
        If pointer is None, self.pointer is used
        """
        pass
    def delete(self, pointer=None):
        """DELETE a row_obj corresponding to 'pointer'
        Check that all primary keys are contained in the row
        If pointer is None, self.pointer is used
        """
        pass

    def insert(self, row={}):
        """INSERT a new row. row is a dict field_name:value
        Check that all primary keys are inside the row
        """
        pass

    def check_prim_keys(self, pointer=None):
        """Check that the row is completely defined, ie: all primary keys are
        present in the specification.
        May be useless when using res_obj from mappers?...
        """
        pass
    def count(self):
        """return number of rows in the res_obj. Note that in case of a join
        len(res_obj) only gives the number of instance of the class of the
        primary class of the mapper, not the number of row of the mapper in the
        normal sql way
        count depend on how index has been created (left=True|False)
        """
        return len(self.index)
    
#     def next(self):
#         self.current += 1
#         try:
#             return self.get()
#         except:
#             raise StopIteration
      

    
    def __getitem__(self, item):
        return self.get()
    
    def create_index(self, res=None, lvl=0, left=True):
        """Create a list of all the indexes to rows
        left=False will be equivalent to a normal join
        left=True (default) will be equivalent to a LEFT (outer?) JOIN
        """
        #sd.debug("lvl: %s" % lvl)
        if lvl == 0:
            tot=0
            self.pre = {}
            self.index = []
            self.left = left

        if lvl > 10:
            #sd.debug("max-lvl raggiunto: %s" % lvl)
            sys.exit()
        if not res:
            res=self.res_obj

        props = []
        try:
            props = reflect.get_props(res[0].mapper)
        except:
            pass

        x = 0
        for R in res:
            ## self.pre is a dictionary that holds the position or each
            ##    level
            self.pre[lvl] = x

            ## if any props loop there too
            for prop in props:
                #sd.debug( "create_index - prop: %s" % prop)
                rp = getattr(R, prop[0])
#                if prop[1] == PropertyLoader.ONETOMANY:
                if prop[1] == ONETOMANY:
                    ### NESTED CALL
                    if len(rp) > 0:
                        self.create_index(rp, lvl=lvl+1) 
                    else: 
                        if self.left:
                            idx = [self.pre[y] for y in range(lvl+1)]
                            #sd.debug(idx)
                            self.index.append(idx)
#                 if len(rp) > 0:
#                     self.create_index(rp, lvl=lvl+1) 
#                 elif self.left:
#                     idx = [self.pre[y] for y in range(lvl+1)]
#                     self.index.append(idx)
            if not props:
                ## ie: no more loops to get in
                idx = [self.pre[y] for y in range(lvl+1)]
                self.index.append(idx)

            x += 1

        if lvl == 0:
            return len(self.index)
    
        
