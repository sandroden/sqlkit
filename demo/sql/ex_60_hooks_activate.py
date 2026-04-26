"""hooks/on_activate

on_activate is run when you press Return in the field.

"""

class Validation(object):

    def on_activate__first_name(self, mask, field_name, field):
        print(("his name is %s and he comes from %s" % (
            field.get_value(), mask.get_value('nation'))))

    on_activate__last_name = on_activate__first_name

t = SqlMask(model.Director, dbproxy=db,
            order_by='last_name', hooks=Validation())

t.reload()
