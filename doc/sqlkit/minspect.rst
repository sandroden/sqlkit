InspectMapper 
=============

   InspectMapper is used (w/ autoloading) to inspect the structure of the db
   relative to the mapper used. InspectMapper has the following methods:
   
InspectMapper methods
----------------------
   :keys: 
       returns all the keys (field_names) present in the mapper

   :tables: 
       return the table names present in the mapper. If mode='mapper'
       it will return the mapper of each table

   :table_fields(table_name):  
       return all the fields in 'table_name' 

   :get_mapper(table_name): 
       return the mapper for 'table_name'

   :get_class(table_name): 
       return the class for 'table_name'

   :get_pkeys(table_name): 
       return a list for all pkeys of table_name

InspectMapper attributes
-------------------------

   InspectMapper provides several attributes, one for each field_name. Each
   attribute is a dictionary with the following keys:

            :table_name:    mapper.table.name ,
            :name:          field_name,
            :table:         mapper.table ,
            :pg_type:       type(mapper.c[field_name].type), 
            :type:          self.pytype[type(mapper.c[field_name].type)],
            :col_spec:      mapper.c[field_name].type.get_col_spec(),
            :is_serial:     is_serial(mapper.c[field_name]),
            :property:      property,
            :fkey:          (table, field_name) or False,
            :pkey:          mapper.c[field_name].primary_key,
            :mapper:        mapper,
	    :length:        in case of strings fields,

