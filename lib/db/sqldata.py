####### SqlData
# pointer: this is a key element to retrieve a mapper (as iter in a treeview)
# pointer is a list whose length depends on how may properties are there
# connecting to other ClassObject (rows)
# the order in which 

import sys
import sqlalchemy
import dbg
import inspect



ONETOMANY = 0
MANYTOONE = 1

class MissingPointerError(Exception): pass
class PrimaryKeyUpdateError(Exception): pass
    
class NotUniqueResultFromSelectError(Exception): pass
class MissingValueFromSelectError(Exception): pass

class SqlData(object):
    """main data manipulation interface

    SqlData Allows to browse inside data of a rowset as returned by mapper.select()
    it firstly creates ad index of pointers to class instances. You can use those
    pointers or an index to UPDATE/DELETE data.
    Index is an int within self.pointers a list of pointer.
    A  pointer is a list of instances.
    
    """
    __metaclass__ = dbg.LogTheMethods
    pointer_info = None
    index = None  # dict of all pointers

    def __init__(self, res_obj, mapper_info, session, left=True, fields=None):
        self.res_obj = res_obj
        self.session = session
        self.mapper_info = mapper_info
        self._create_pointers(left=left)
        self.deleted = []
        self.current = 0
        if not fields:
            fields = self.mapper_info.fields
        self.field_list = fields
        
        #tables = mapper_info.tables()
        #for t in tables:
        #    dbg.write("Table: %s => %s" % (t, mapper_info.table_fields(t)))
        
        
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
        #dbg.write()
        #dbg.write('LEN pointers:', len(self.pointers))
        R = {}
        if index is not None:
            self.current = index
        while self.current + incr in self.deleted:
            self.current += incr

        if self.current+incr < 0:
            return


        try:
            pointer = self.pointers[self.current+incr]
            self.current += incr
        except IndexError:
            #dbg.write("IndexError")
            return
        #dbg.write("current: %s" % (self.current))

        for cl_instance in pointer:
            R.update( self._instance2dict(cl_instance) )

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
        self.current = 0
        
    def all_as_dicts(self):
        """print all the records"""
        dicts = []
        for i in range(len(self.pointers)):
            #print self.get(index=i, mode='dict')
            dicts.append(self.get(index=i, mode='dict'))
        self.current = 0
        #print dicts
        return dicts
        
    def _instance2dict(self, instance):
        """return a dict representing the data of an instance. If the instance has
        a property representing a MANYTOONE relation it returns those values too,
        if the relation represent a ONETOMANY it calls itself recursevly.
        """
        #dbg.write(instance._managed_attributes)
        R = {}
        for f in instance.c.keys():
            R[f] = getattr(instance, f)

        return R
    
#         MANYTOONE_attrs = [f for f in instance._managed_attributes
#                      if f not in instance.c.keys() and
#                      type(instance._managed_attributes[f]) == sqlalchemy.attributes.ScalarAttribute ]
#         #dbg.write("props %s" % M21_attrs)
#         for prop in MANYTOONE_attrs:
#             prop_attr = getattr(instance, prop)
#             if prop_attr == None:
#                 ## in a join the record connected via this property can be missing
#                 ## in this case we want to 'empty' all fields
#                 for f in self.mapper_info.prop_fields(prop):
#                     R[f] = None
#             else:
#                 for f in prop_attr.c.keys():
#                     R[f] = getattr(prop_attr, f) 
                
#         return R
    
    def _dict2instance(self, instance, R):
        """set values of an instance. If the instance has
        a property representing a MANYTOONE relation it sets those values too,
        if the relation represent a ONETOMANY it calls itself recursevly.
        """
        #dbg.write("R -1 %s" % R)
        self._set_value_loop(instance, R)
                

        return R
#         MANYTOONE_attrs = [f for f in instance._managed_attributes
#                      if f not in instance.c.keys() and
#                      type(instance._managed_attributes[f]) == sqlalchemy.attributes.ScalarAttribute ]
#         #dbg.write("props %s" % MANYTOONE_attrs)
#         for prop in MANYTOONE_attrs:
#             prop_attr = getattr(instance, prop)
#             if prop_attr == None:
#                 continue
#             self._set_value_loop(prop_attr, R, m2o=True, parent=instance)
# #             for f in prop_attr.c.keys():
# #                 self._set_value(prop_attr, f, R, m2o=True, parent=instance)
                
        return R
    def _set_value_loop(self, instance, R, m2o=False, parent=None):
        """Chek if is a primaryKey and try to handle it if mto (many2one) 
        attach a different instance to the object
        """
        #dbg.write("R: %s" % R)
        ## if primaryKey, mapper will silently ignore it...
        #dbg.write(f)

        ### firstly parse PKeys so that if a _change_sun happens it will happen
        ### before any other change and further update will be applied to the
        ### correct instance

        pkeys = [k for k in instance.c.keys() if self.mapper_info[k]['pkey'] ]
        keys = list(pkeys)
        keys += [k for k in instance.c.keys() if not self.mapper_info[k]['pkey'] ]

        for f in keys:
            if f in R:
                #dbg.write("f: %s" % f)
                if self.mapper_info[f]['pkey']:
                    if m2o:
                        self._change_sun(instance, f, R, parent, pkeys)
                        return
                    else:
                        raise PrimaryKeyUpdateError(
                            "Primary keys are immutable " + \
                            " in sqlalchemy (sigh!) - %s is PKey" % f)
                            
                #dbg.write('setattr(instance, %s, %s' % (f, R[f]))
                setattr(instance, f, R[f])
                
    def _change_sun(self, instance, f, R, parent, pkeys):
        """attach a new class instance if the PKey of an object related with
        many2one is used
        """

        tbl    = self.mapper_info[f]['table_name']
        mapper = self.mapper_info[f]['mapper']
        ### FIXME: pkeys is here to check that we are issuing a select that has
        ### all the pkeys: to implement
        ret = self.session.query(mapper).select(
            "%s = :%s" % (f, f), params={ f : R[f] } )
        length = len(ret)
        if length == 0:
            raise MissingValueFromSelectError(
                "No tuples in table %s with PKey: %s" % (tbl, R[f]))
        if length > 1:
            raise NotUniqueResultFromSelectError(
                "Too many tuples in table %s with PKey: %s" % (tbl, R[f]))
        if length == 1:
            #dbg.write("Imposto %s a %s"%(f , ret))
            setattr(parent, f, ret[0])
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
        #dbg.write()

        if index is not None:
            pointer = self.pointers[index]

        if not pointer:
            dbg.write('current', self.current)
            pointer = self.pointers[self.current]
            #dbg.write("uso index self.current: %s" % self.current)
            #raise MissingPointerError('A pointer is needed', pointer)

        #dbg.write("Pointer: %s" % pointer)

        for instance in pointer:
            self._dict2instance(instance, R)

                
    def Rshow(self, instance):
        for k in self.mapper_info.keys():
            dbg.write(k, getattr(instance, k, '++'))
            
    def delete(self, index=None, pointer=None):
        """delete a record. For each pointer it only deletes the last item
        """
        if index is not None:
            pointer = self.pointers[index]

        if not pointer:
            pointer = self.pointers[self.current]
            index = self.current = self.pointers.index(pointer)
            #raise MissingPointerError('A pointer is needed', pointer)

        self.deleted += [index]
        self.session.delete(pointer[-1])
        
    def add(self, R):
        """add a record. Create instances and attach them to first instance
        """
        #dbg.write()
        main_table  = self.mapper_info.tables()[0]
        main_mapper = self.mapper_info.get_mapper(main_table)
        new = self._create_instance(main_table, R)
        #for i in new.c.keys():
        #    dbg.write("%s => %s" % (i, getattr(new,i)))
        self.pointers.append([new])
        self.current = len(self.pointers)-1
        #dbg.write("new", new, "current", self.current, self.pointers[self.current])
        self.session.save(new)
        return new
        ## attach other instances
        for prop in inspect.get_props(main_mapper):
            table_name = main_mapper.props[prop[0]].target.name
            if prop[1] == ONETOMANY:
                getattr(new, prop[0]).append(self._create_instance(table_name, R))
            
    def _create_instance(self, tbl, R):
        """ create an instance"""
        #dbg.write("R: %s, type: %s" % (R, type(R)))
        class_name = self.mapper_info.get_class(tbl)
        inst = class_name()
        
        for field in self.mapper_info.table_fields(tbl):
            if field in R:
                #dbg.write(field, R[field])
                setattr(inst, field, R[field])

        
        return inst
                        
    def get_current(self):
        return self.pointers[self.current]
    
    def index(self):
        return self.current
    
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
        return len(self.pointers)
    
    def __getitem__(self, item):
        return self.get()
    
    def _create_pointers(self, res=None, lvl=0, left=True):
        """Create a list of all the pointers to rows
        left=False will be equivalent to a normal join
        left=True (default) will be equivalent to a LEFT (outer?) JOIN

        Returns the lenth of the list
        """
        #dbg.write("lvl: %s" % lvl)
        if lvl == 0:
            tot=0
            self.pre = {}
            self.pointers = []
            self.left = left

        if lvl > 10:
            #dbg.write("max-lvl raggiunto: %s" % lvl)
            sys.exit()
        if not res:
            res=self.res_obj

        if not res:
            # we are building and empty sqldata structure as when starting a SqlMask
            return
        
        props = []
        try:
            props = inspect.get_props(res[0].mapper)
        except:
            pass

        x = 0
        for R in res:
            ## self.pre is a dictionary that holds the position or each
            ##    level
            self.pre[lvl] = R

            ## if any props loop there too
            for prop in props:
                #dbg.write( "_create_pointers - prop: %s" % prop)
                rp = getattr(R, prop[0])
#                if prop[1] == PropertyLoader.ONETOMANY:
                if prop[1] == ONETOMANY:
                    ### NESTED CALL
                    if len(rp) > 0:
                        self._create_pointers(rp, lvl=lvl+1) 
                    else: 
                        if self.left:
                            idx = [self.pre[y] for y in range(lvl+1)]
                            #dbg.write(idx)
                            self.pointers.append(idx)
                #else:
                    #dbg.write("rp: %s keys: %s" % (rp, self.show(rp)))

#                 if len(rp) > 0:
#                     self._create_pointers(rp, lvl=lvl+1) 
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
    
        
    def show(self, record):
        return ["%s:%s" %(i,getattr(record, i)) for i in record.c.keys()]
