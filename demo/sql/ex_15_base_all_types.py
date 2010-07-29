"""base/all types

simple mask showing all supported types. Some are clearly poorely rendered.


"""

lay = """
{|.text  varchar10   varchar200
         text        - -
         uni
         uni_text    - -
         }

{|.date
         date        time
#         datetime    datetime_tz
         datetime    
         time        time_tz
         interval
         }

{|.numbers
         integer
         float        numeric
         }
{|.boolean
         bool         bool_null
         }
         
"""

t = SqlMask(model.AllTypes, layout=lay, dbproxy=db )
t.reload()


for label in ('text','date','numbers','boolean'):
    frame = t.widgets['F.%s' % label]
    frame.set_label('a')
    frame.get_property('label-widget').set_markup(
        '<b><i>%s</i></b>' % label)


t = SqlTable(model.AllTypes, dbproxy=db )
t.reload()



