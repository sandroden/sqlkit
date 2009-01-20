#!/usr/bin/python

from  sqlkit.widgets import *
import gtk
import movies


field_list="integer, float numeric"
t = SqlTable(table=movies.AllTypes.__table__, dbproxy=movies.db,
             field_list=field_list, single=True)
t.reload()


gtk.main()


