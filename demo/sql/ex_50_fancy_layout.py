"""layout/fancy layout

A more complex layout, that uses notebook.

The description language may look unusual at first, but you'll soon
realize that in *many* circumstances it's enough for a database application
and lets you test several different layouts in minutes.

You can also see how to add other gtk widgets and connect them

"""


lay = """
   varchar10   b=Who_Am_I
   varchar200  - - -
   {N  { %time
         {>>.general

            date        interval
            datetime    time
            }
         {>.hidden_boolean
            bool    bool_null
         }
        }
      {  %numbers
         integer
         float
         numeric
      }
      {  %text
         text
         uni_text
       }
       } - - - 
   

"""
t = SqlMask(model.AllTypes, dbproxy=db, layout=lay)

def close(widget, window):
    print("The End for me...")
    window.destroy()

t.widgets['b=Who_Am_I'].connect('clicked', close, t.widgets['Window'])
t.reload()
