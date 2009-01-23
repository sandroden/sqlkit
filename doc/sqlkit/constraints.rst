.. _constraints:

============
Constraints
============

Constraints are a mean to limit browsing of data to a limited set. It's a
different concept from filtering, as this enforces a limitation while
filtering allows the user to change the values at will.

A constraint can be as simple as::

  t = SqlTable(table='movie', dbproxy=db)
  t.add_constraints(actors__country='ITA', genres__name='drama',
    year__gte=1950, year__lte=1970)

And browsing of movies will be constrained into dramas with at least one
Italian actor, produced between 1950 and 1970. The double underscore '__'
will allow spanning from one table to a related one (provided a relation was
established at sqlalchemy level) and from attribute name to operator to be
used.  

.. note::

  the same syntax can be used to add filters on :ref:`completion <filter_completion>`


query
=======

limitation acts on ``self.query`` directly. Self query can be modified in
any way accepted by ``sqlalchemy`` syntax 

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

  from sqlkit.db.django_syntax import django2sqlalchemy
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


API
----

.. automodule:: sqlkit.db.django_syntax

.. autofunction:: django2sqlalchemy


Native sqlalchemy constraint
============================

The django syntax is in no way the only possibility. If that is not
sufficient to express the constraints you need you can just use any filter
on the query directly::

   tk_tbl = ticket.Ticket.__table__
   my_id = self.db.get_session().query(ticket.User).filter_by(username=setup.USERNAME).one().id

   t = sk.SqlTable(Class=ticket.Ticket, field_list=field_list, order_by='priority', **self.meta)
   t.add_filter(status=1)
   t.query = t.query.filter(or_(tk_tbl.c['assigned_by_id'] == my_id ,
                                tk_tbl.c['assigned_to_id'] == my_id , ))


this example shows how to force a constraint on ticket requiring that the
ticket be assigned *by* or *to* USERNAME. Any further filter applyed
interactively will be applied *on top* of this constraint. This is
equivalent to writing::

   t.add_constraint(assigned_by_id=my_id, assigned_to_id=my_id, OR=True)

At the moment of this writing it's not possible to write::

   t.add_constraint(assigned_by_id__username=USERNAME)

as the foreign key relation is not followed in this context.

