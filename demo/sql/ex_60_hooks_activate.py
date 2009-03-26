"""hooks/on_activate

on_activate if run when you press Return in the field.

"""

class Director(SqlMask):
    def on_activate__first_name(self, field_name, field):
        print "he's name is %s and comes from %s" % (
            field.get_value(), self.get_value('nation'))

t = Director(class_=model.Director, dbproxy=db, )

t.reload()

