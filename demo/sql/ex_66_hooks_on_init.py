"""hooks/on_init

in this example, on_init is used to configure callback on button 'b=ciao'
that is only present in the mask that will pop up if you right click on a row


"""
from sqlkit.db.utils import get_differences

class Hooks(object):

    def on_init(self, sqlwidget):

        sqlwidget.completions.director_id.group_by = 'nation'
        sqlwidget.gui_fields.year.format = '#'
        

        
        if sqlwidget.is_mask():
            button = sqlwidget.widgets['b=ciao']
            button.connect('clicked', self.button_clicked_cb)

    def button_clicked_cb(self, widget):
        print "Ciao, mondo"

lay = """
   title
   year
   director_id
   b=ciao -
"""

t = SqlTable(class_=model.Movie, dbproxy=db, layout=lay,
             order_by='title', hooks=Hooks(),)
t.reload()

