"""hooks/on_init

in this example, on_init is used to configure callback on button 'b=ciao'
that is only present in the mask that will pop up if you right click on a row

Registering a hook
------------------

note that here we have registered the hook rather than passing it to the
sqlwidget. The advantage is that it will be used by *any* widget that is
created. Of course you should be carefull in using this feature as any
contraints will be enforced in any sqlwidgete of that table.

"""
from sqlkit.db.utils import get_differences
from sqlkit.db import register_hook

class Hooks(object):

    def on_init(self, sqlwidget):

        sqlwidget.completions.director_id.group_by = 'nation'
        sqlwidget.gui_fields.year.format = '#'
        

        
        if sqlwidget.is_mask():
            button = sqlwidget.widgets['b=ciao']
            button.connect('clicked', self.button_clicked_cb)

    def button_clicked_cb(self, widget):
        print "Ciao, mondo"


register_hook('movie', Hooks)

lay = """
   title
   year
   director_id
   b=ciao -
"""

t = SqlTable(model.Movie, dbproxy=db, layout=lay,
             order_by='title')
t.reload()

