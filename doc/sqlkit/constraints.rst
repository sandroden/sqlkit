.. _constraints:

============
Constraints
============

A contraint can be as simple as::

  t = SqlTable(table='movie', dbproxy=db)
  t.add_constraints(actors__country='ITA', genres__name='drama',
    year__gte=1950, year__lte=1970)

And browsing of movies will be constrained into dramas with at least one
italian actor, produced between 1950 and 1970. The double underscore '__'
will allow spanning from one table to a related (provided a relation was
established at sqlalchemy level) and from attribute name to operator to be
used.  

operators
---------

these operators are recognized::

  OPERATORS = {
    'like' : 'like',
    'lt'   : '<',
    'gt'   :  '>',
    'lte'  : '<=',
    'gte'  : '>=',
    'eq'   : '=',
    'neq'   : '!=',
    'equal': '=',
    'in'   : 'IN',
  }

and ``icontains`` that at the moment map to ``match`` sqlalchemy operators
that in turn map to database specific info.

conjunctions
------------

In the example all conditions have been ``AND`` ed. It's possible to use
``OR`` operator adding ``or_=True``  argument.

django2sqlalchemy
-----------------

You can get a sqlalchemy ``ClauseList`` object starting from a django-like
expression using django2sqlalchemy function::

  from sqlkit.db.sql import django2sqlalchemy
  clause_list, join_paths = django2sqlalchemy(mapper, *args)

where ``args`` can be or_=boolean or any django-like query.
Django2sqlalchemy returns a tuple: (clause_list, join_path):

  :clause_list: 
     the list of column expression connected with ``AND`` or
     ``OR`` according to ``or_`` argument
  :join_path:
     the list of path needed to add to query via ``query.join()`` to
     have all the fields the query needs to apply the filters in clause_list 

     A possibility is to add::
     
        for path in join_path:
	   query.join(path).reset_joinpoint()




     
