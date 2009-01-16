#!/usr/bin/python

from  sqlkit.widgets import *
import gtk
import movies


#     id             = Column(Integer(), primary_key=True)
#     varchar10      = Column(String(10))
#     varchar200     = Column(String(200))
#     text           = Column(Text())
#     uni            = Column(Unicode(10, assert_unicode=False))
#     uni_text       = Column(UnicodeText(assert_unicode=False))
#     date           = Column(Date())
#     datetime       = Column(DateTime())
#     interval       = Column(Interval())
#     time           = Column(Time(timezone=False))
#     integer        = Column(Integer())
#     float          = Column(Float())
#     numeric        = Column(Numeric(8,2))
#     bool           = Column(Boolean, nullable=False)
#     bool_null      = Column(Boolean, nullable=True)

field_list="date, varchar10, varchar200, datetime"
t = SqlTable(table=movies.AllTypes.__table__, dbproxy=movies.db,
             field_list=field_list, single=True)
#t.reload()


gtk.main()


