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



ONETOMANY = 0
MANYTOONE = 1

class MissingPointerError(Exception):
    pass

class SqlData(object):
    """main data manipulation interface

    SqlData Allows to browse inside data of a rowset retured by mapper.select()
    it firstly creates ad index of pointers to class instances. You can use those
    pointers or an index to UPDATE/DELETE data.
    Index is and int within self.pointers a list of pointer.
    A  pointer is a list of instances.
    
    """
    pointer_info = None
    index = None  # dict of all pointers

    def __init__(self, res_obj, mapper_info, left=True, fields=None):
        self.res_obj = res_obj
        self.mapper_info = mapper_info
        self.create_pointers(left=left)
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
        return self.get(mode=mode, fields=fields, incr = -1)

    def get(self, index=None, pointer=[], mode='dict', fields=None, incr=0):
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
            pointer = self.pointers[self.current]
        except IndexError:
            self.current -= 1
            return
        #sd.debug("current: %s - %s" % (self.current, idx ))

        for cl_instance in pointer:
            R.update( self.instance2dict(cl_instance) )

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

    def printall(self, mode='values'):
        """print all the records, mainly for debug"""
        for i in range(len(self.pointers)):
            print self.get(index=i, mode=mode)

    def instance2dict(self, instance):
        """return a dict representing the data of an instance. If the instance has
        a property representing a MANYTOONE relation it returns those values too,
        if the relation represent a ONETOMANY it calls itself recursevly.
        """
        #sd.debug(instance)
        R = {}
        for f in instance.c.keys():
            R[f] = getattr(instance, f)

        MANYTOONE_attrs = [f for f in instance._managed_attributes
                     if f not in instance.c.keys() and
                     type(instance._managed_attributes[f]) == sqlalchemy.attributes.ScalarAttribute ]
        #sd.debug("props %s" % M21_attrs)
        for prop in MANYTOONE_attrs:
            prop_attr = getattr(instance, prop)
            for f in prop_attr.c.keys():
                R[f] = getattr(prop_attr, f) 
                
        return R

    def dict2instance(self, instance, R):
        """set values of an instance. If the instance has
        a property representing a MANYTOONE relation it sets those values too,
        if the relation represent a ONETOMANY it calls itself recursevly.
        """
        #sd.debug(instance)
        for f in instance.c.keys():
            if f in R:
                setattr(instance, f, R[f])

        MANYTOONE_attrs = [f for f in instance._managed_attributes
                     if f not in instance.c.keys() and
                     type(instance._managed_attributes[f]) == sqlalchemy.attributes.ScalarAttribute ]
        #sd.debug("props %s" % M21_attrs)
        for prop in MANYTOONE_attrs:
            prop_attr = getattr(instance, prop)
            for f in prop_attr.c.keys():
                if f in R:
                    setattr(prop_attr, f, R[f]) 
                
        return R

    def fields(self, fields):
        """sets the list of fields that will be returned"""
        self.field_list = fields

    def set(self, R,  pointer=[], index=None):
        """receive a pointer or an index a dict whose keys are the field_name
        and whose values are the new values and UPDATE the corresponding
        row_obj.
        Check that all primary keys are contained in the row.
        If pointer is None, self.pointer is used
        """
        # sd.debug("index: %s pointer: %s" % (index, pointer))
        if index is not None:
            pointer = self.pointers[index]

        if not pointer:
            raise MissingPointerError('A pointer is needed', pointer)

        for instance in pointer:
            self.dict2instance(instance, R)
                

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
    
    def __getitem__(self, item):
        return self.get()
    
    def create_pointers(self, res=None, lvl=0, left=True):
        """Create a list of all the pointers to rows
        left=False will be equivalent to a normal join
        left=True (default) will be equivalent to a LEFT (outer?) JOIN

        Returns the lenth o the list
        """
        #sd.debug("lvl: %s" % lvl)
        if lvl == 0:
            tot=0
            self.pre = {}
            self.pointers = []
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
            self.pre[lvl] = R

            ## if any props loop there too
            for prop in props:
                #sd.debug( "create_pointers - prop: %s" % prop)
                rp = getattr(R, prop[0])
#                if prop[1] == PropertyLoader.ONETOMANY:
                if prop[1] == ONETOMANY:
                    ### NESTED CALL
                    if len(rp) > 0:
                        self.create_pointers(rp, lvl=lvl+1) 
                    else: 
                        if self.left:
                            idx = [self.pre[y] for y in range(lvl+1)]
                            #sd.debug(idx)
                            self.pointers.append(idx)
#                 if len(rp) > 0:
#                     self.create_pointers(rp, lvl=lvl+1) 
#                 elif self.left:
#                     idx = [self.pre[y] for y in range(lvl+1)]
#                     self.pointers.append(idx)
            if not props:
                ## ie: no more loops to get in
                idx = [self.pre[y] for y in range(lvl+1)]
                self.pointers.append(idx)

            x += 1

        if lvl == 0:
            return len(self.pointers)
    
        
