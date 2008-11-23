.. _defaults:

==========
Defaults
==========

Defaults are a handy way to avoid typing too much. Defaults are handled by
sqlkit.db.defaults.Default class::

 def_visita = defaults.Defaults('cliente_visita', metadata=elixir.metadata)
 def_visita.set_defaults( {'data' : def_visita.now, 'telefonata' : True})
 def_visita.fk('venditore_id', 'username', 'mauro')
 def_visita.fk('negozio_id', 'negozio', 'Macherio')


Defaults class requires a table name and a metaclass to know where to
autoload/read table definition. 

set_default
===========

The main method is ``set_defaults`` that
requires a dictionary as argument with *field_name* as keys and *field
defaults* as value.

fk
===

Default in foreign key are set literally via ``fk``. It will follow the
reference and find the correct value

now & today
=============

attributes ``now`` and ``today`` will be substituted appropriately when
creating the field


SA defaults & server defaults
=============================

At the moment Sqlalchemy defaults are handled only in case of a fixed value
(not a callable) and defaults defined in the server as well.
