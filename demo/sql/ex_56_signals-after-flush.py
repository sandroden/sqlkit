"""signals/after-flush

after-flush is triggered from withing SessionExtension as after_flush method.
It's emitted when flushing has occurred but state of the session still retains
all info on objects: session.dirty, session.new, session.deleted are available
and ach object has info on it's history

"""


t = SqlTable(class_=model.Director, dbproxy=db, )

def after_flush_cb(sqlwidget, obj, session):
    from sqlkit.db.utils import get_differences

    for o in session.new:
        print "New object: %s" % o
    for o in session.dirty:
        print "Updated objects: %s" % o
        for field_name, old, new in get_differences(o, sqlwidget.session):
            print "%s: %s ==> %s" % (field_name, old, new)
        
    for o in session.deleted:
        print "Deleted objects: %s" % o


t.connect('after-flush', after_flush_cb)
t.reload()

